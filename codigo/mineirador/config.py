"""
config.py — Configuração do minerador via variáveis de ambiente.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MinerConfig:
    """Centraliza todas as configurações do minerador.

    Lê as variáveis de ambiente definidas no .env e expõe
    propriedades tipadas para o resto do módulo.
    """

    owner: str = field(default_factory=lambda: os.environ["OWNER"])
    repo: str = field(default_factory=lambda: os.environ["REPO"])
    token: str = field(default_factory=lambda: os.environ.get("GITHUB_TOKEN", ""))
    output_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "dados"))
    )
    cache_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "dados")) / "cache"
    )

    # Quantos itens por página nas chamadas paginadas (máx. 100 pela API)
    per_page: int = 100

    # Pausa entre requisições para não estourar o rate-limit (segundos)
    request_delay: float = 0.1
    

    #após iniciar o mineirador ele vai chamar os métodos para criar as pastas de dados mineirados e dados cache 
    def __post_init__(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property #@property transforma o método em um atrbibuto, meio que a função irá retornar uma variável
    def repo_full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def output_file(self) -> Path:
        return self.output_dir / "interacoes.json"

    @property
    def has_token(self) -> bool:
        return bool(self.token)
    