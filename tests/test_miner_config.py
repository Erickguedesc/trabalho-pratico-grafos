import pytest

from codigo.mineirador.config import MinerConfig


def _base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OWNER", "alice")
    monkeypatch.setenv("REPO", "myrepo")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKENS", raising=False)


def test_token_unico_via_github_token(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_abc123")
    config = MinerConfig()
    assert config.tokens == ["ghp_abc123"]
    assert config.has_token is True


def test_multiplos_tokens_via_github_tokens(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GITHUB_TOKENS", "tok1,tok2, tok3 ")
    config = MinerConfig()
    assert config.tokens == ["tok1", "tok2", "tok3"]


def test_github_tokens_tem_prioridade_sobre_github_token(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GITHUB_TOKENS", "multi1,multi2")
    monkeypatch.setenv("GITHUB_TOKEN", "single")
    config = MinerConfig()
    assert config.tokens == ["multi1", "multi2"]


def test_sem_token_has_token_e_falso(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    config = MinerConfig()
    assert config.tokens == []
    assert config.has_token is False


def test_repo_full_name(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("OWNER", "starship")
    monkeypatch.setenv("REPO", "starship")
    config = MinerConfig()
    assert config.repo_full_name == "starship/starship"


def test_output_file_path(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    config = MinerConfig()
    assert config.output_file == tmp_path / "interacoes.json"


def test_post_init_cria_diretorios(monkeypatch, tmp_path):
    output_dir = tmp_path / "dados"
    monkeypatch.setenv("OWNER", "alice")
    monkeypatch.setenv("REPO", "myrepo")
    monkeypatch.setenv("OUTPUT_DIR", str(output_dir))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKENS", raising=False)
    config = MinerConfig()
    assert config.output_dir.exists()
    assert config.cache_dir.exists()


def test_owner_ausente_lanca_key_error(monkeypatch, tmp_path):
    monkeypatch.delenv("OWNER", raising=False)
    monkeypatch.setenv("REPO", "myrepo")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    with pytest.raises(KeyError):
        MinerConfig()


def test_github_tokens_com_entrada_vazia_e_ignorada(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GITHUB_TOKENS", "tok1,,  ,tok2")
    config = MinerConfig()
    assert config.tokens == ["tok1", "tok2"]
