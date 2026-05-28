"""
json_cache.py — Cache em disco para respostas da API do GitHub.

Evita re-coletar dados já baixados em execuções anteriores,
economizando quota do rate-limit.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CacheJson:
    """Lê e grava respostas JSON indexadas por uma chave de cache.

    Estrutura em disco:
        cache_dir/
            issues.json
            issues_comments_123.json
            pulls.json
            pulls_reviews_456.json
            ...
    """

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any | None:
        """Retorna o objeto em cache ou None se não existir."""
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            logger.debug("Cache HIT: %s", key)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache corrompido para '%s': %s — ignorando.", key, exc)
            path.unlink(missing_ok=True)
            return None

    def set(self, key: str, data: Any) -> None:
        """Persiste *data* em disco sob *key*."""
        path = self._path(key)
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            logger.debug("Cache WRITE: %s", key)
        except OSError as exc:
            logger.warning("Não foi possível gravar cache '%s': %s", key, exc)

    def has(self, key: str) -> bool:
        """Verifica se a chave existe em cache."""
        return self._path(key).exists()

    def invalidate(self, key: str) -> None:
        """Remove uma entrada do cache."""
        self._path(key).unlink(missing_ok=True)

    def clear(self) -> None:
        """Apaga todo o cache."""
        for f in self._dir.glob("*.json"):
            f.unlink(missing_ok=True)
        logger.info("Cache limpo.")

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _path(self, key: str) -> Path:
        # Sanitiza a chave para ser um nome de arquivo válido
        safe_key = key.replace("/", "_").replace(" ", "_")
        return self._dir / f"{safe_key}.json"