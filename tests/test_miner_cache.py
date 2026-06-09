import json

import pytest

from codigo.mineirador.json_cache import CacheJson


def test_get_retorna_none_quando_chave_inexistente(tmp_path):
    cache = CacheJson(tmp_path)
    assert cache.get("inexistente") is None


def test_set_e_get_roundtrip(tmp_path):
    cache = CacheJson(tmp_path)
    data = [{"login": "alice"}, {"login": "bob"}]
    cache.set("usuarios", data)
    assert cache.get("usuarios") == data


def test_has_retorna_true_quando_chave_existe(tmp_path):
    cache = CacheJson(tmp_path)
    cache.set("chave", {"x": 1})
    assert cache.has("chave") is True


def test_has_retorna_false_quando_chave_inexistente(tmp_path):
    cache = CacheJson(tmp_path)
    assert cache.has("chave") is False


def test_invalidate_remove_entrada(tmp_path):
    cache = CacheJson(tmp_path)
    cache.set("chave", [1, 2, 3])
    cache.invalidate("chave")
    assert cache.get("chave") is None
    assert cache.has("chave") is False


def test_invalidate_em_chave_inexistente_nao_lanca_erro(tmp_path):
    cache = CacheJson(tmp_path)
    cache.invalidate("nao_existe")


def test_clear_apaga_todo_cache(tmp_path):
    cache = CacheJson(tmp_path)
    cache.set("a", [1])
    cache.set("b", [2])
    cache.clear()
    assert list(tmp_path.glob("*.json")) == []


def test_get_json_corrompido_retorna_none_e_remove_arquivo(tmp_path):
    cache = CacheJson(tmp_path)
    corrupt_file = tmp_path / "corrompido.json"
    corrupt_file.write_text("{ INVALIDO", encoding="utf-8")
    result = cache.get("corrompido")
    assert result is None
    assert not corrupt_file.exists()


def test_chave_com_barra_e_sanitizada(tmp_path):
    cache = CacheJson(tmp_path)
    cache.set("owner/repo", [{"n": 1}])
    assert cache.has("owner/repo") is True
    assert cache.get("owner/repo") == [{"n": 1}]


def test_chave_com_espaco_e_sanitizada(tmp_path):
    cache = CacheJson(tmp_path)
    cache.set("issue comments 123", {"ok": True})
    assert cache.get("issue comments 123") == {"ok": True}


def test_set_sobrescreve_valor_existente(tmp_path):
    cache = CacheJson(tmp_path)
    cache.set("k", [1, 2])
    cache.set("k", [3, 4])
    assert cache.get("k") == [3, 4]


def test_diretorio_e_criado_se_nao_existir(tmp_path):
    nested = tmp_path / "nivel1" / "nivel2"
    cache = CacheJson(nested)
    assert nested.exists()
