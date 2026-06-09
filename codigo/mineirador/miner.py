"""
miner.py — Orquestrador principal do minerador.

Responsabilidades:
  - Coordena GitHubClient para coletar todos os tipos de interação
  - Transforma as respostas brutas da API no contrato JSON do projeto
  - Grava o arquivo dados/interacoes.json
  - Exibe progresso no terminal

Contrato de saída (uma linha por interação):
{
    "source_user": str,   # quem iniciou a ação
    "target_user": str,   # quem recebeu a ação
    "type": str,          # issue_comment | pr_comment | issue_close |
                          #   pr_open | pr_review | pr_merge
    "weight": int,        # 2 | 3 | 4 | 5
    "repo": str,          # "owner/repo"
    "created_at": str     # ISO 8601
}
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .config import MinerConfig
from .github_client import GitHubClient
from .json_cache import CacheJson

logger = logging.getLogger(__name__)

_WEIGHT = {
    "issue_comment": 2,
    "pr_comment":    2,
    "issue_close":   3,
    "pr_open":       3,
    "pr_review":     4,
    "pr_merge":      5,
}


@dataclass
class Interaction:
    """Representa uma interação entre dois usuários."""

    source_user: str
    target_user: str
    type: str
    weight: int
    repo: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "source_user": self.source_user,
            "target_user": self.target_user,
            "type": self.type,
            "weight": self.weight,
            "repo": self.repo,
            "created_at": self.created_at,
        }


class GitHubMinerador:
    """Minera interações de um repositório GitHub e salva em JSON."""

    def __init__(self, config: MinerConfig) -> None:
        self._config = config
        self._cache = CacheJson(config.cache_dir)
        self._client = GitHubClient(config, self._cache)

    # ------------------------------------------------------------------
    # Ponto de entrada
    # ------------------------------------------------------------------

    def run(self) -> Path:
        """Executa a mineração completa e retorna o caminho do arquivo gerado."""
        logger.info("Iniciando mineração de %s", self._config.repo_full_name)

        interactions = list(self._mine_issue_interactions())
        interactions.extend(self._mine_pr_interactions())

        valid = [
            i for i in interactions
            if i.source_user and i.target_user and i.source_user != i.target_user
        ]

        output = self._config.output_file
        self._save(valid, output)
        logger.info("Mineração concluída. %d interações válidas salvas em %s", len(valid), output)
        return output

    # ------------------------------------------------------------------
    # Issues — usa endpoints bulk para eliminar o padrão N+1
    # ------------------------------------------------------------------

    def _mine_issue_interactions(self) -> Iterator[Interaction]:
        issues = self._client.get_all_issues()
        issue_authors = self._build_issue_author_map(issues)
        logger.info("Issues (puras) encontradas: %d", len(issue_authors))

        yield from self._issue_comment_interactions(issue_authors)
        yield from self._issue_close_interactions(issue_authors)

    def _build_issue_author_map(self, issues: list[dict]) -> dict[int, str]:
        return {
            i["number"]: self._login(i.get("user"))
            for i in issues
            if "pull_request" not in i and self._login(i.get("user"))
        }

    def _issue_comment_interactions(
        self, issue_authors: dict[int, str]
    ) -> Iterator[Interaction]:
        for comment in self._client.get_all_issue_comments():
            issue_number = int(comment["issue_url"].rsplit("/", 1)[-1])
            issue_author = issue_authors.get(issue_number)
            commenter = self._login(comment.get("user"))
            if not issue_author or not commenter:
                continue
            yield Interaction(
                source_user=commenter,
                target_user=issue_author,
                type="issue_comment",
                weight=_WEIGHT["issue_comment"],
                repo=self._config.repo_full_name,
                created_at=comment.get("created_at", ""),
            )

    def _issue_close_interactions(
        self, issue_authors: dict[int, str]
    ) -> Iterator[Interaction]:
        seen: set[int] = set()
        for event in self._client.get_all_issue_events():
            if event.get("event") != "closed":
                continue
            issue_obj = event.get("issue") or {}
            issue_number = issue_obj.get("number")
            if not issue_number or issue_number in seen:
                continue
            issue_author = issue_authors.get(issue_number)
            closer = self._login(event.get("actor"))
            if issue_author and closer and closer != issue_author:
                seen.add(issue_number)
                yield Interaction(
                    source_user=closer,
                    target_user=issue_author,
                    type="issue_close",
                    weight=_WEIGHT["issue_close"],
                    repo=self._config.repo_full_name,
                    created_at=event.get("created_at", ""),
                )

    # ------------------------------------------------------------------
    # Pull Requests — bulk para comentários; per-PR apenas para revisões
    # ------------------------------------------------------------------

    def _mine_pr_interactions(self) -> Iterator[Interaction]:
        pulls = self._client.get_all_pulls()
        pr_info = self._build_pr_info_map(pulls)
        logger.info("Pull requests encontrados: %d", len(pr_info))

        yield from self._pr_open_interactions(pr_info)
        yield from self._pr_comment_interactions(pr_info)
        yield from self._pr_review_and_merge_interactions(pr_info)

    def _build_pr_info_map(self, pulls: list[dict]) -> dict[int, dict]:
        result = {}
        for pr in pulls:
            author = self._login(pr.get("user"))
            if not author:
                continue
            result[pr["number"]] = {
                "author": author,
                "merged_by": self._login(pr.get("merged_by")),
                "merged_at": pr.get("merged_at"),
                "assignees": pr.get("assignees") or [],
                "created_at": pr.get("created_at", ""),
            }
        return result

    def _pr_open_interactions(self, pr_info: dict[int, dict]) -> Iterator[Interaction]:
        for info in pr_info.values():
            pr_author = info["author"]
            pr_target = info["merged_by"] or self._first_assignee(info["assignees"], pr_author)
            if pr_target and pr_target != pr_author:
                yield Interaction(
                    source_user=pr_author,
                    target_user=pr_target,
                    type="pr_open",
                    weight=_WEIGHT["pr_open"],
                    repo=self._config.repo_full_name,
                    created_at=info["created_at"],
                )

    def _pr_comment_interactions(self, pr_info: dict[int, dict]) -> Iterator[Interaction]:
        for comment in self._client.get_all_pull_review_comments():
            pr_number = int(comment["pull_request_url"].rsplit("/", 1)[-1])
            info = pr_info.get(pr_number)
            commenter = self._login(comment.get("user"))
            if not info or not commenter:
                continue
            yield Interaction(
                source_user=commenter,
                target_user=info["author"],
                type="pr_comment",
                weight=_WEIGHT["pr_comment"],
                repo=self._config.repo_full_name,
                created_at=comment.get("created_at", ""),
            )

    def _pr_review_and_merge_interactions(
        self, pr_info: dict[int, dict]
    ) -> Iterator[Interaction]:
        for pr_number, info in pr_info.items():
            yield from self._pr_review_interactions(pr_number, info)
            if info["merged_at"] and info["merged_by"]:
                yield Interaction(
                    source_user=info["merged_by"],
                    target_user=info["author"],
                    type="pr_merge",
                    weight=_WEIGHT["pr_merge"],
                    repo=self._config.repo_full_name,
                    created_at=info["merged_at"],
                )

    def _pr_review_interactions(self, pr_number: int, info: dict) -> Iterator[Interaction]:
        for review in self._client.get_pull_reviews(pr_number):
            reviewer = self._login(review.get("user"))
            state = review.get("state", "").upper()
            if reviewer and state in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED"):
                yield Interaction(
                    source_user=reviewer,
                    target_user=info["author"],
                    type="pr_review",
                    weight=_WEIGHT["pr_review"],
                    repo=self._config.repo_full_name,
                    created_at=review.get("submitted_at", ""),
                )

    # ------------------------------------------------------------------
    # Persistência e helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _save(interactions: list[Interaction], path: Path) -> None:
        """Grava as interações em formato JSON Lines (uma por linha)."""
        with path.open("w", encoding="utf-8") as fh:
            for interaction in interactions:
                fh.write(json.dumps(interaction.to_dict(), ensure_ascii=False) + "\n")

    def _first_assignee(self, assignees: list[dict], exclude: str) -> str:
        for assignee in assignees:
            candidate = self._login(assignee)
            if candidate and candidate != exclude:
                return candidate
        return ""

    @staticmethod
    def _login(user_obj: dict | None) -> str:
        if not user_obj:
            return ""
        return user_obj.get("login", "")


# ------------------------------------------------------------------
# Entry-point direto
# ------------------------------------------------------------------

def main() -> None:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    config = MinerConfig()
    miner = GitHubMinerador(config)
    miner.run()


if __name__ == "__main__":
    main()
