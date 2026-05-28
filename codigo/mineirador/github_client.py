"""
github_client.py — Cliente HTTP para a API REST do GitHub.

Responsabilidades:
  - Autenticação via token Bearer
  - Paginação automática (Link: rel="next")
  - Respeito ao rate-limit (detecta 403/429 e aguarda)
  - Cache transparente via CacheJson
"""
from __future__ import annotations

import logging
import time
import urllib.parse
import urllib.request
import urllib.error
import json
from typing import Any

from .config import MinerConfig
from .json_cache import CacheJson

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.github.com"


class RateLimitError(Exception):
    """Levantada quando o rate-limit é atingido e não há retry possível."""


class GitHubClient:
    """Abstrai chamadas paginadas à API REST do GitHub.

    Parâmetros
    ----------
    config:
        Configuração do minerador (token, per_page, request_delay).
    cache:
        Instância de CacheJson para armazenar respostas em disco.
    """

    def __init__(self, config: MinerConfig, cache: CacheJson) -> None:
        self._config = config
        self._cache = cache

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get_all_issues(self) -> list[dict]:
        """Retorna todas as issues (abertas + fechadas) do repositório."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/issues",
            params={"state": "all", "per_page": self._config.per_page},
            cache_key="issues",
        )

    def get_issue_comments(self, issue_number: int) -> list[dict]:
        """Retorna todos os comentários de uma issue específica."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/issues/{issue_number}/comments",
            params={"per_page": self._config.per_page},
            cache_key=f"issue_comments_{issue_number}",
        )

    def get_all_pulls(self) -> list[dict]:
        """Retorna todos os pull requests (abertos + fechados) do repositório."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/pulls",
            params={"state": "all", "per_page": self._config.per_page},
            cache_key="pulls",
        )

    def get_pull_comments(self, pull_number: int) -> list[dict]:
        """Retorna os comentários de revisão (inline) de um PR."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/pulls/{pull_number}/comments",
            params={"per_page": self._config.per_page},
            cache_key=f"pull_comments_{pull_number}",
        )

    def get_pull_reviews(self, pull_number: int) -> list[dict]:
        """Retorna as revisões (approve/request_changes/comment) de um PR."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/pulls/{pull_number}/reviews",
            params={"per_page": self._config.per_page},
            cache_key=f"pull_reviews_{pull_number}",
        )

    def get_issue_events(self, issue_number: int) -> list[dict]:
        """Retorna os eventos de uma issue (usado para detectar fechamentos)."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/issues/{issue_number}/events",
            params={"per_page": self._config.per_page},
            cache_key=f"issue_events_{issue_number}",
        )

    # ------------------------------------------------------------------
    # Paginação
    # ------------------------------------------------------------------

    def _get_paged(
        self,
        endpoint: str,
        params: dict[str, Any],
        cache_key: str,
    ) -> list[dict]:
        """Baixa todas as páginas de um endpoint e retorna lista achatada.

        Se já houver cache válido, devolve diretamente sem bater na API.
        """
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        results: list[dict] = []
        url: str | None = self._build_url(endpoint, params)

        while url:
            data, next_url = self._fetch_page(url)
            if isinstance(data, list):
                results.extend(data)
            url = next_url
            if url:
                time.sleep(self._config.request_delay)

        self._cache.set(cache_key, results)
        return results

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _fetch_page(self, url: str) -> tuple[Any, str | None]:
        """Faz uma única requisição GET e devolve (data, próxima_url)."""
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if self._config.has_token:
            req.add_header("Authorization", f"Bearer {self._config.token}")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                data = json.loads(raw)
                next_url = self._parse_next_link(resp.headers.get("Link", ""))
                return data, next_url

        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                retry_after = int(exc.headers.get("Retry-After", 60))
                logger.warning(
                    "Rate-limit atingido. Aguardando %ds...", retry_after
                )
                time.sleep(retry_after)
                return self._fetch_page(url)  # tenta novamente

            logger.error("HTTP %s ao acessar %s: %s", exc.code, url, exc.reason)
            raise

        except urllib.error.URLError as exc:
            logger.error("Erro de rede ao acessar %s: %s", url, exc.reason)
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_url(endpoint: str, params: dict[str, Any]) -> str:
        query = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
        return f"{_BASE_URL}{endpoint}?{query}"

    @staticmethod
    def _parse_next_link(link_header: str) -> str | None:
        """Extrai a URL de próxima página do cabeçalho Link da API do GitHub.

        Formato: <https://api.github.com/...?page=2>; rel="next", ...
        """
        if not link_header:
            return None
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                url_part = part.split(";")[0].strip()
                return url_part.strip("<>")
        return None