import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from codigo.mineirador.config import MinerConfig
from codigo.mineirador.github_client import GitHubClient, RateLimitError
from codigo.mineirador.json_cache import CacheJson


def _make_config(tmp_path, tokens=None):
    return MinerConfig(
        owner="alice",
        repo="myrepo",
        tokens=tokens or [],
        output_dir=tmp_path,
        cache_dir=tmp_path / "cache",
        request_delay=0.0,
        max_retries=2,
    )


def _mock_response(data, link_header=""):
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.headers.get.side_effect = lambda key, default="": link_header if key == "Link" else default
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _http_error(code, retry_after="1"):
    hdrs = MagicMock()
    hdrs.get.side_effect = lambda k, d="": {"Retry-After": retry_after}.get(k, d)
    err = urllib.error.HTTPError(url="http://x", code=code, msg="err", hdrs=hdrs, fp=None)
    err.headers = hdrs
    return err


# ------------------------------------------------------------------
# Métodos estáticos
# ------------------------------------------------------------------

def test_parse_next_link_extrai_proxima_url():
    link = '<https://api.github.com/repos/a/b?page=2>; rel="next", <...>; rel="last"'
    result = GitHubClient._parse_next_link(link)
    assert result == "https://api.github.com/repos/a/b?page=2"


def test_parse_next_link_retorna_none_sem_next():
    link = '<https://api.github.com/repos/a/b?page=1>; rel="prev"'
    assert GitHubClient._parse_next_link(link) is None


def test_parse_next_link_retorna_none_em_string_vazia():
    assert GitHubClient._parse_next_link("") is None


def test_build_url_monta_url_com_query_string():
    url = GitHubClient._build_url("/repos/a/b/issues", {"state": "all", "per_page": "100"})
    assert url.startswith("https://api.github.com/repos/a/b/issues?")
    assert "state=all" in url
    assert "per_page=100" in url


# ------------------------------------------------------------------
# Rotação de tokens
# ------------------------------------------------------------------

def test_current_token_retorna_vazio_sem_tokens(tmp_path):
    client = GitHubClient(_make_config(tmp_path, tokens=[]), CacheJson(tmp_path / "cache"))
    assert client._current_token == ""


def test_current_token_retorna_token_unico(tmp_path):
    client = GitHubClient(_make_config(tmp_path, tokens=["tk1"]), CacheJson(tmp_path / "cache"))
    assert client._current_token == "tk1"


def test_rotate_token_alterna_entre_tokens(tmp_path):
    client = GitHubClient(_make_config(tmp_path, tokens=["t1", "t2", "t3"]), CacheJson(tmp_path / "cache"))
    assert client._current_token == "t1"
    client._rotate_token()
    assert client._current_token == "t2"
    client._rotate_token()
    assert client._current_token == "t3"
    client._rotate_token()
    assert client._current_token == "t1"


def test_rotate_token_nao_muda_com_token_unico(tmp_path):
    client = GitHubClient(_make_config(tmp_path, tokens=["unico"]), CacheJson(tmp_path / "cache"))
    client._rotate_token()
    assert client._current_token == "unico"


# ------------------------------------------------------------------
# Cache
# ------------------------------------------------------------------

def test_get_paged_retorna_cache_sem_http(tmp_path):
    config = _make_config(tmp_path)
    cache = CacheJson(tmp_path / "cache")
    cache.set("issues", [{"number": 1}])
    client = GitHubClient(config, cache)

    with patch("codigo.mineirador.github_client.urllib.request.urlopen") as mock_urlopen:
        result = client.get_all_issues()
        mock_urlopen.assert_not_called()

    assert result == [{"number": 1}]


def test_get_paged_salva_resultado_no_cache(tmp_path):
    config = _make_config(tmp_path)
    cache = CacheJson(tmp_path / "cache")
    client = GitHubClient(config, cache)

    with patch("codigo.mineirador.github_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _mock_response([{"number": 42}])
        result = client.get_all_issues()

    assert result == [{"number": 42}]
    assert cache.get("issues") == [{"number": 42}]


def test_get_paged_percorre_multiplas_paginas(tmp_path):
    config = _make_config(tmp_path)
    cache = CacheJson(tmp_path / "cache")
    client = GitHubClient(config, cache)

    base = "https://api.github.com/repos/alice/myrepo/issues"
    page1_link = f'<{base}?page=2>; rel="next"'

    with patch("codigo.mineirador.github_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [
            _mock_response([{"number": 1}], link_header=page1_link),
            _mock_response([{"number": 2}]),
        ]
        result = client.get_all_issues()

    assert len(result) == 2
    assert result[0]["number"] == 1
    assert result[1]["number"] == 2


# ------------------------------------------------------------------
# Rate limit e retry
# ------------------------------------------------------------------

@patch("codigo.mineirador.github_client.time.sleep")
def test_fetch_page_rate_limit_faz_retry_e_retorna(mock_sleep, tmp_path):
    config = _make_config(tmp_path, tokens=["t1", "t2"])
    cache = CacheJson(tmp_path / "cache")
    client = GitHubClient(config, cache)

    with patch("codigo.mineirador.github_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [
            _http_error(429, retry_after="5"),
            _mock_response([{"ok": True}]),
        ]
        data, next_url = client._fetch_page("https://api.github.com/repos/alice/myrepo/issues")

    assert data == [{"ok": True}]
    mock_sleep.assert_called_with(5)


@patch("codigo.mineirador.github_client.time.sleep")
def test_fetch_page_max_retries_lanca_rate_limit_error(mock_sleep, tmp_path):
    config = _make_config(tmp_path, tokens=["t1"])
    cache = CacheJson(tmp_path / "cache")
    client = GitHubClient(config, cache)

    with patch("codigo.mineirador.github_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = _http_error(403)

        with pytest.raises(RateLimitError):
            client._fetch_page("https://api.github.com/repos/alice/myrepo/issues")


def test_fetch_page_http_error_nao_429_relanca_excecao(tmp_path):
    config = _make_config(tmp_path)
    cache = CacheJson(tmp_path / "cache")
    client = GitHubClient(config, cache)

    with patch("codigo.mineirador.github_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = _http_error(404)

        with pytest.raises(urllib.error.HTTPError):
            client._fetch_page("https://api.github.com/repos/alice/myrepo/issues")
