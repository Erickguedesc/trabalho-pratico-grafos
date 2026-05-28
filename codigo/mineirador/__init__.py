"""
minerador — Coleta interações de repositórios GitHub e grava em JSON.
"""
from .config import MinerConfig
from .json_cache import CacheJson
from .github_client import GitHubClient
from .miner import GitHubMinerador, Interaction

__all__ = [
    "MinerConfig",
    "CacheJson",
    "GitHubClient",
    "GitHubMinerador",
    "Interaction",
]