"""config.py — Configuração do minerador via variáveis de ambiente."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _read_tokens() -> list[str]:
    multi = os.environ.get("GITHUB_TOKENS", "")
    if multi:
        return [t.strip() for t in multi.split(",") if t.strip()]
    single = os.environ.get("GITHUB_TOKEN", "")
    return [single] if single else []


@dataclass
class MinerConfig:
    """Centraliza todas as configurações do minerador."""

    owner: str = field(default_factory=lambda: os.environ["OWNER"])
    repo: str = field(default_factory=lambda: os.environ["REPO"])
    tokens: list[str] = field(default_factory=_read_tokens)
    output_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "dados"))
    )
    cache_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "dados")) / "cache"
    )

    per_page: int = 100
    # 5.000 req/h por token ≈ 1,38 req/s; base de 0,75 s dividida pelo número
    # de tokens para aproveitar o round-robin sem estourar o rate-limit.
    request_delay: float = field(default=0.0, init=False)
    max_retries: int = 3

    def __post_init__(self) -> None:
        self.request_delay = 0.75 / max(1, len(self.tokens))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def repo_full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def output_file(self) -> Path:
        return self.output_dir / "interacoes.json"

    @property
    def has_token(self) -> bool:
        return bool(self.tokens)
