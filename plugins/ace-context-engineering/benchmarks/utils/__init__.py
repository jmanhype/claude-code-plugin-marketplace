"""
Benchmarks utilities for ACE framework implementation.
"""

from .base_method import AdaptiveMethod
from .bullet_retriever import BulletRetriever
from .skills_executor import SkillsExecutor
from .appworld_executor import AppWorldExecutor, APPWORLD_AVAILABLE
from .reflector import Reflector
from .curator import Curator  # Old curator (for backwards compatibility)
from .curator_staged import StagedCurator  # New three-stage curator
from .embeddings import EmbeddingsDeduplicator  # TF-IDF fallback

try:
    from .embeddings_faiss import FAISSDeduplicator  # FAISS-based (recommended)
except Exception as e:
    FAISSDeduplicator = None
    print(f"⚠️  FAISS-based deduplicator unavailable: {e}")

from .claude_code_method import ClaudeCodeACE

__all__ = [
    'AdaptiveMethod',
    'BulletRetriever',
    'SkillsExecutor',
    'AppWorldExecutor',
    'APPWORLD_AVAILABLE',
    'Reflector',
    'Curator',
    'StagedCurator',
    'EmbeddingsDeduplicator',
    'FAISSDeduplicator',
    'ClaudeCodeACE',
]
