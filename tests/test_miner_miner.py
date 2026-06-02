import json
from unittest.mock import MagicMock

import pytest

from codigo.mineirador.config import MinerConfig
from codigo.mineirador.miner import GitHubMinerador


def _make_config(tmp_path):
    return MinerConfig(
        owner="alice",
        repo="myrepo",
        tokens=[],
        output_dir=tmp_path,
        cache_dir=tmp_path / "cache",
        request_delay=0.0,
        max_retries=1,
    )


def _user(login):
    return {"login": login}


# ------------------------------------------------------------------
# Utilitários estáticos
# ------------------------------------------------------------------

def test_login_extrai_login_do_usuario():
    assert GitHubMinerador._login({"login": "alice"}) == "alice"


def test_login_retorna_vazio_para_none():
    assert GitHubMinerador._login(None) == ""


def test_login_retorna_vazio_para_dict_sem_login():
    assert GitHubMinerador._login({"id": 1}) == ""


# ------------------------------------------------------------------
# _build_issue_author_map
# ------------------------------------------------------------------

def test_build_issue_author_map_exclui_pull_requests(tmp_path):
    miner = GitHubMinerador(_make_config(tmp_path))
    issues = [
        {"number": 1, "user": _user("alice"), "state": "open"},
        {"number": 2, "user": _user("bob"), "pull_request": {"url": "..."}},
    ]
    result = miner._build_issue_author_map(issues)
    assert 1 in result
    assert 2 not in result


def test_build_issue_author_map_exclui_issues_sem_usuario(tmp_path):
    miner = GitHubMinerador(_make_config(tmp_path))
    issues = [
        {"number": 1, "user": None},
        {"number": 2, "user": _user("carol")},
    ]
    result = miner._build_issue_author_map(issues)
    assert 1 not in result
    assert result[2] == "carol"


# ------------------------------------------------------------------
# _first_assignee
# ------------------------------------------------------------------

def test_first_assignee_retorna_primeiro_valido_nao_excluido(tmp_path):
    miner = GitHubMinerador(_make_config(tmp_path))
    assignees = [_user("alice"), _user("bob")]
    assert miner._first_assignee(assignees, exclude="alice") == "bob"


def test_first_assignee_retorna_vazio_se_todos_sao_o_excluido(tmp_path):
    miner = GitHubMinerador(_make_config(tmp_path))
    assignees = [_user("alice"), _user("alice")]
    assert miner._first_assignee(assignees, exclude="alice") == ""


def test_first_assignee_retorna_vazio_com_lista_vazia(tmp_path):
    miner = GitHubMinerador(_make_config(tmp_path))
    assert miner._first_assignee([], exclude="alice") == ""


# ------------------------------------------------------------------
# run() — integração completa com cliente mockado
# ------------------------------------------------------------------

def _make_mock_client():
    """Cria um cliente com dados que cobrem todos os 6 tipos de interação."""
    client = MagicMock()

    client.get_all_issues.return_value = [
        {"number": 1, "user": _user("alice"), "state": "closed"},
        {"number": 2, "user": _user("bob"), "state": "open"},
        {"number": 99, "user": _user("ghost"), "pull_request": {"url": "..."}},
    ]

    client.get_all_issue_comments.return_value = [
        {"issue_url": "https://api.github.com/repos/x/y/issues/1",
         "user": _user("carol"), "created_at": "2024-01-01T10:00:00Z"},
        # auto-interação: será filtrada em run()
        {"issue_url": "https://api.github.com/repos/x/y/issues/2",
         "user": _user("bob"), "created_at": "2024-01-02T10:00:00Z"},
    ]

    client.get_all_issue_events.return_value = [
        # primeiro fechamento de issue #1
        {"event": "closed", "actor": _user("dave"),
         "issue": {"number": 1, "user": _user("alice")},
         "created_at": "2024-01-03T10:00:00Z"},
        # segundo fechamento da mesma issue — deve ser ignorado
        {"event": "closed", "actor": _user("eve"),
         "issue": {"number": 1, "user": _user("alice")},
         "created_at": "2024-01-04T10:00:00Z"},
        {"event": "labeled", "actor": _user("frank"),
         "issue": {"number": 2}, "created_at": "2024-01-05T10:00:00Z"},
    ]

    client.get_all_pulls.return_value = [
        {"number": 100, "user": _user("george"), "merged_by": _user("henry"),
         "merged_at": "2024-02-01T10:00:00Z", "assignees": [],
         "created_at": "2024-01-20T10:00:00Z"},
        {"number": 101, "user": _user("ivan"), "merged_by": None,
         "merged_at": None, "assignees": [_user("judy")],
         "created_at": "2024-01-21T10:00:00Z"},
    ]

    client.get_all_pull_review_comments.return_value = [
        {"pull_request_url": "https://api.github.com/repos/x/y/pulls/100",
         "user": _user("kate"), "created_at": "2024-01-25T10:00:00Z"},
    ]

    client.get_pull_reviews.side_effect = lambda n: (
        [{"user": _user("leo"), "state": "APPROVED", "submitted_at": "2024-01-26T10:00:00Z"}]
        if n == 100 else []
    )

    return client


def test_run_gera_arquivo_de_interacoes(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    output = miner.run()

    assert output.exists()
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    interactions = [json.loads(line) for line in lines]
    assert len(interactions) > 0


def test_run_filtra_auto_interacoes(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    miner.run()
    lines = (tmp_path / "interacoes.json").read_text(encoding="utf-8").strip().splitlines()
    interactions = [json.loads(l) for l in lines]

    for i in interactions:
        assert i["source_user"] != i["target_user"]


def test_run_produz_todos_os_tipos_de_interacao(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    miner.run()
    lines = (tmp_path / "interacoes.json").read_text(encoding="utf-8").strip().splitlines()
    types_found = {json.loads(l)["type"] for l in lines}

    assert "issue_comment" in types_found
    assert "issue_close" in types_found
    assert "pr_open" in types_found
    assert "pr_comment" in types_found
    assert "pr_review" in types_found
    assert "pr_merge" in types_found


def test_run_registra_apenas_primeiro_fechamento_por_issue(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    miner.run()
    lines = (tmp_path / "interacoes.json").read_text(encoding="utf-8").strip().splitlines()
    closures = [json.loads(l) for l in lines if json.loads(l)["type"] == "issue_close"]

    issue1_closures = [c for c in closures if c["target_user"] == "alice"]
    assert len(issue1_closures) == 1
    assert issue1_closures[0]["source_user"] == "dave"


def test_run_pr_open_usa_assignee_quando_sem_merged_by(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    miner.run()
    lines = (tmp_path / "interacoes.json").read_text(encoding="utf-8").strip().splitlines()
    pr_opens = [json.loads(l) for l in lines if json.loads(l)["type"] == "pr_open"]

    ivan_open = next((p for p in pr_opens if p["source_user"] == "ivan"), None)
    assert ivan_open is not None
    assert ivan_open["target_user"] == "judy"


def test_run_merge_usa_peso_correto(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    miner.run()
    lines = (tmp_path / "interacoes.json").read_text(encoding="utf-8").strip().splitlines()
    merges = [json.loads(l) for l in lines if json.loads(l)["type"] == "pr_merge"]

    assert all(m["weight"] == 5 for m in merges)


def test_run_nao_gera_merge_para_pr_nao_mergeado(tmp_path):
    config = _make_config(tmp_path)
    miner = GitHubMinerador(config)
    miner._client = _make_mock_client()

    miner.run()
    lines = (tmp_path / "interacoes.json").read_text(encoding="utf-8").strip().splitlines()
    merges = [json.loads(l) for l in lines if json.loads(l)["type"] == "pr_merge"]

    assert all(m["source_user"] == "henry" for m in merges)
