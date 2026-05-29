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

# Pesos conforme o enunciado
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
    """Minera interações de um repositório GitHub e salva em JSON.

    Parâmetros
    ----------
    config:
        MinerConfig com credenciais e caminhos.
    """

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

        interactions: list[Interaction] = []

        interactions.extend(self._mine_issue_interactions())
        interactions.extend(self._mine_pr_interactions())

        # Filtra auto-interações (source == target) e interações sem usuário
        valid = [
            i for i in interactions
            if i.source_user and i.target_user and i.source_user != i.target_user
        ]

        output = self._config.output_file
        self._save(valid, output)

        logger.info(
            "Mineração concluída. %d interações válidas salvas em %s",
            len(valid),
            output,
        )
        return output

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def _mine_issue_interactions(self) -> Iterator[Interaction]:
        """Minera comentários e fechamentos de issues."""
        issues = self._client.get_all_issues()
        # A API de /issues retorna PRs também; filtra apenas issues reais
        pure_issues = [i for i in issues if "pull_request" not in i]

        logger.info("Issues encontradas: %d", len(pure_issues))

        for issue in pure_issues:
            issue_number = issue["number"]
            issue_author = self._login(issue.get("user"))
            if not issue_author:
                continue

            # — Comentários em issue (peso 2) ——————————————————————————
            comments = self._client.get_issue_comments(issue_number)
            for comment in comments:
                commenter = self._login(comment.get("user"))
                if not commenter:
                    continue
                yield Interaction(
                    source_user=commenter,
                    target_user=issue_author,
                    type="issue_comment",
                    weight=_WEIGHT["issue_comment"],
                    repo=self._config.repo_full_name,
                    created_at=comment.get("created_at", ""),
                )

            # — Fechamento por outro usuário (peso 3) ——————————————————
            if issue.get("state") == "closed":
                events = self._client.get_issue_events(issue_number)
                for event in events:
                    if event.get("event") != "closed":
                        continue
                    closer = self._login(event.get("actor"))
                    if closer and closer != issue_author:
                        yield Interaction(
                            source_user=closer,
                            target_user=issue_author,
                            type="issue_close",
                            weight=_WEIGHT["issue_close"],
                            repo=self._config.repo_full_name,
                            created_at=event.get("created_at", ""),
                        )
                        break  # só o primeiro evento de fechamento

    # ------------------------------------------------------------------
    # Pull Requests
    # ------------------------------------------------------------------

    def _mine_pr_interactions(self) -> Iterator[Interaction]:
        """Minera abertura, comentários, revisões e merges de PRs."""
        pulls = self._client.get_all_pulls()
        logger.info("Pull requests encontrados: %d", len(pulls))

        for pr in pulls:
            pr_number = pr["number"]
            pr_author = self._login(pr.get("user"))
            if not pr_author:
                continue

            # — Abertura de PR (peso 3) ——————————————————————————————
            # A interação registrada é: o autor do PR interage com o
            # repositório notificando os colaboradores. Representamos isso
            # como o autor interagindo com o merger (quem costuma integrar
            # o trabalho). Quando não há merger definido ainda, usamos o
            # primeiro revisor encontrado; se nenhum existir, pulamos.
            pr_target = self._login(pr.get("merged_by"))
            if not pr_target:
                # tenta o assignee como alvo substituto
                assignees = pr.get("assignees") or []
                for assignee in assignees:
                    candidate = self._login(assignee)
                    if candidate and candidate != pr_author:
                        pr_target = candidate
                        break

            if pr_target and pr_target != pr_author:
                yield Interaction(
                    source_user=pr_author,
                    target_user=pr_target,
                    type="pr_open",
                    weight=_WEIGHT["pr_open"],
                    repo=self._config.repo_full_name,
                    created_at=pr.get("created_at", ""),
                )

            # — Comentários inline em PR (peso 2) ————————————————————
            pr_comments = self._client.get_pull_comments(pr_number)
            for comment in pr_comments:
                commenter = self._login(comment.get("user"))
                if not commenter:
                    continue
                yield Interaction(
                    source_user=commenter,
                    target_user=pr_author,
                    type="pr_comment",
                    weight=_WEIGHT["pr_comment"],
                    repo=self._config.repo_full_name,
                    created_at=comment.get("created_at", ""),
                )

            # — Revisões / aprovações (peso 4) ————————————————————————
            reviews = self._client.get_pull_reviews(pr_number)
            for review in reviews:
                reviewer = self._login(review.get("user"))
                if not reviewer:
                    continue

                state = review.get("state", "").upper()

                if state in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED"):
                    yield Interaction(
                        source_user=reviewer,
                        target_user=pr_author,
                        type="pr_review",
                        weight=_WEIGHT["pr_review"],
                        repo=self._config.repo_full_name,
                        created_at=review.get("submitted_at", ""),
                    )

            # — Merge (peso 5) ——————————————————————————————————————
            if pr.get("merged_at"):
                merger = self._login(pr.get("merged_by"))
                if merger:
                    yield Interaction(
                        source_user=merger,
                        target_user=pr_author,
                        type="pr_merge",
                        weight=_WEIGHT["pr_merge"],
                        repo=self._config.repo_full_name,
                        created_at=pr.get("merged_at", ""),
                    )

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    @staticmethod
    def _save(interactions: list[Interaction], path: Path) -> None:
        """Grava as interações em formato JSON Lines (uma por linha)."""
        with path.open("w", encoding="utf-8") as fh:
            for interaction in interactions:
                fh.write(json.dumps(interaction.to_dict(), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _login(user_obj: dict | None) -> str:
        """Extrai o login de um objeto usuário da API, ou '' se ausente."""
        if not user_obj:
            return ""
        # Bots e apps do GitHub têm tipo "Bot"; podemos filtrá-los se quiser
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