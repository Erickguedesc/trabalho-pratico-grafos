"""
github_client.py — Cliente HTTP para a API REST do GitHub.

Responsabilidades:
  - Autenticação via token Bearer com rotação entre múltiplos tokens
  - Throttle global de requisições para respeitar o rate-limit
  - Paginação automática (Link: rel="next")
  - Retry iterativo em caso de 403/429 ou erros de rede
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
    """Levantada quando o número máximo de tentativas é atingido."""


class GitHubClient:
    """Abstrai chamadas paginadas à API REST do GitHub."""

    def __init__(self, config: MinerConfig, cache: CacheJson) -> None:
        self._config = config
        self._cache = cache
        self._token_index = 0
        self._last_request_time = 0.0

    # ------------------------------------------------------------------
    # Rotação de tokens
    # ------------------------------------------------------------------

    @property
    def _current_token(self) -> str:
        if not self._config.tokens:
            return ""
        return self._config.tokens[self._token_index % len(self._config.tokens)]

    def _rotate_token(self) -> None:
        if len(self._config.tokens) > 1:
            self._token_index = (self._token_index + 1) % len(self._config.tokens)

    # ------------------------------------------------------------------
    # API pública — endpoints de listagem (bulk)
    # ------------------------------------------------------------------

    def get_all_issues(self) -> list[dict]:
        """Retorna todas as issues (abertas + fechadas) do repositório."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/issues",
            params={"state": "all", "per_page": self._config.per_page},
            cache_key="issues",
        )

    def get_all_issue_comments(self) -> list[dict]:
        """Retorna todos os comentários de todas as issues em uma única paginação."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/issues/comments",
            params={"per_page": self._config.per_page},
            cache_key="issues_comments_bulk",
        )

    def get_all_issue_events(self) -> list[dict]:
        """Retorna todos os eventos de todas as issues em uma única paginação."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/issues/events",
            params={"per_page": self._config.per_page},
            cache_key="issues_events_bulk",
        )

    def get_all_pulls(self) -> list[dict]:
        """Retorna todos os pull requests (abertos + fechados) do repositório."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/pulls",
            params={"state": "all", "per_page": self._config.per_page},
            cache_key="pulls",
        )

    def get_all_pull_review_comments(self) -> list[dict]:
        """Retorna todos os comentários inline de todos os PRs em uma única paginação."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/pulls/comments",
            params={"per_page": self._config.per_page},
            cache_key="pulls_comments_bulk",
        )

    def get_pull_reviews(self, pull_number: int) -> list[dict]:
        """Retorna as revisões de um PR específico (não há endpoint bulk disponível)."""
        return self._get_paged(
            endpoint=f"/repos/{self._config.repo_full_name}/pulls/{pull_number}/reviews",
            params={"per_page": self._config.per_page},
            cache_key=f"pull_reviews_{pull_number}",
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
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        results: list[dict] = []
        url: str | None = self._build_url(endpoint, params)

        while url:
            data, url = self._fetch_page(url)
            if isinstance(data, list):
                results.extend(data)

        self._cache.set(cache_key, results)
        return results

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        wait = self._config.request_delay - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_time = time.monotonic()

    def _fetch_page(self, url: str) -> tuple[Any, str | None]:
        """Faz uma única requisição GET com retry iterativo."""
        for attempt in range(self._config.max_retries + 1):
            self._throttle()
            req = self._build_request(url)
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read())
                    next_url = self._parse_next_link(resp.headers.get("Link", ""))
                self._rotate_token()
                return data, next_url

            except urllib.error.HTTPError as exc:
                if exc.code in (403, 429):
                    self._rotate_token()
                    retry_after = int(exc.headers.get("Retry-After", 60))
                    logger.warning(
                        "Rate-limit atingido. Aguardando %ds... (tentativa %d/%d)",
                        retry_after, attempt + 1, self._config.max_retries,
                    )
                    time.sleep(retry_after)
                    continue
                logger.error("HTTP %s ao acessar %s: %s", exc.code, url, exc.reason)
                raise

            except urllib.error.URLError as exc:
                if attempt < self._config.max_retries:
                    logger.warning(
                        "Erro de rede (%s). Retentando em 5s... (tentativa %d/%d)",
                        exc.reason, attempt + 1, self._config.max_retries,
                    )
                    time.sleep(5)
                    continue
                logger.error("Erro de rede ao acessar %s: %s", url, exc.reason)
                raise

            except (TimeoutError, OSError) as exc:
                # TimeoutError é subclasse de OSError, não de URLError —
                # por isso precisa de bloco próprio para ser capturado e ter retry.
                if attempt < self._config.max_retries:
                    wait = 10 * (attempt + 1)  # backoff: 10s, 20s, 30s
                    logger.warning(
                        "Timeout ao ler resposta de %s. Aguardando %ds... (tentativa %d/%d)",
                        url, wait, attempt + 1, self._config.max_retries,
                    )
                    time.sleep(wait)
                    continue
                logger.error("Timeout persistente ao acessar %s após %d tentativas.", url, self._config.max_retries)
                raise

        raise RateLimitError(f"Máximo de tentativas atingido para {url}")

    def _build_request(self, url: str) -> urllib.request.Request:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        token = self._current_token
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        return req

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_url(endpoint: str, params: dict[str, Any]) -> str:
        query = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
        return f"{_BASE_URL}{endpoint}?{query}"

    @staticmethod
    def _parse_next_link(link_header: str) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                url_part = part.split(";")[0].strip()
                return url_part.strip("<>")
        return None
