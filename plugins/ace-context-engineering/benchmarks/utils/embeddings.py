"""
Embeddings for semantic similarity and deduplication.

Uses sentence-transformers for semantic similarity (if available),
falls back to TF-IDF for lightweight similarity.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Tuple
import json


class EmbeddingsDeduplicator:
    """
    Performs semantic deduplication using embeddings or TF-IDF fallback.

    Implements grow-and-refine mechanism from ACE paper (Section 3.2).
    """

    def __init__(self, use_embeddings: bool = False):
        """
        Args:
            use_embeddings: If True, use sentence-transformers (requires install).
                           If False, use TF-IDF cosine similarity.
        """
        self.use_embeddings = use_embeddings
        self.model = None

        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Using sentence-transformers for embeddings")
            except ImportError:
                print("sentence-transformers not available, falling back to TF-IDF")
                self.use_embeddings = False

    def find_duplicates(
        self,
        bullets: List[Dict],
        threshold: float = 0.80
    ) -> List[Tuple[str, str, float]]:
        """
        Find duplicate bullets based on semantic similarity.

        Args:
            bullets: List of bullet dictionaries
            threshold: Similarity threshold (0.80 = 80% similar)

        Returns:
            List of (bullet_id_1, bullet_id_2, similarity_score) tuples
        """
        if self.use_embeddings:
            return self._find_duplicates_embeddings(bullets, threshold)
        else:
            return self._find_duplicates_tfidf(bullets, threshold)

    def _find_duplicates_embeddings(
        self,
        bullets: List[Dict],
        threshold: float
    ) -> List[Tuple[str, str, float]]:
        """Find duplicates using sentence embeddings."""
        from sentence_transformers import util

        # Create text representations
        texts = []
        bullet_ids = []
        for b in bullets:
            if b.get('status') != 'active':
                continue
            text = f"{b.get('title', '')} {b.get('content', '')}"
            texts.append(text)
            bullet_ids.append(b['id'])

        # Compute embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=True)

        # Compute pairwise cosine similarities
        similarities = util.cos_sim(embeddings, embeddings)

        # Find pairs above threshold
        duplicates = []
        n = len(bullet_ids)
        for i in range(n):
            for j in range(i + 1, n):
                sim = similarities[i][j].item()
                if sim >= threshold:
                    duplicates.append((bullet_ids[i], bullet_ids[j], sim))

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def _find_duplicates_tfidf(
        self,
        bullets: List[Dict],
        threshold: float
    ) -> List[Tuple[str, str, float]]:
        """Find duplicates using TF-IDF cosine similarity."""
        # Filter active bullets
        active_bullets = [b for b in bullets if b.get('status') == 'active']

        # Build TF-IDF vectors
        docs = [f"{b.get('title', '')} {b.get('content', '')}" for b in active_bullets]
        idf = self._build_idf(docs)
        vectors = [self._tfidf_vec(doc, idf) for doc in docs]

        # Compute pairwise similarities
        duplicates = []
        n = len(active_bullets)
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._cosine(vectors[i], vectors[j])
                if sim >= threshold:
                    duplicates.append((
                        active_bullets[i]['id'],
                        active_bullets[j]['id'],
                        sim
                    ))

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def _tokenize(self, s: str) -> List[str]:
        """Extract tokens from string."""
        return re.findall(r"[a-z0-9]+", s.lower())

    def _build_idf(self, docs: List[str]) -> Dict[str, float]:
        """Build IDF dictionary from documents."""
        df = Counter()
        for doc in docs:
            tokens = set(self._tokenize(doc))
            df.update(tokens)

        N = len(docs)
        return {t: math.log((N + 1) / (c + 1)) + 1 for t, c in df.items()}

    def _tfidf_vec(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        """Compute TF-IDF vector for text."""
        tf = Counter(self._tokenize(text))
        return {t: (tf[t] * idf.get(t, 0.0)) for t in tf}

    def _cosine(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

    def propose_merges(
        self,
        bullets: List[Dict],
        duplicates: List[Tuple[str, str, float]]
    ) -> List[Dict]:
        """
        Propose merge operations for duplicate bullets.

        Strategy:
        - Keep bullet with higher helpful_count
        - Merge content if needed
        - Archive the other bullet

        Returns:
            List of merge operations:
            [{
                'keep_id': 'bullet-123',
                'merge_ids': ['bullet-456'],
                'rationale': '...',
                'merged_content': '...'
            }, ...]
        """
        bullets_by_id = {b['id']: b for b in bullets}
        merges = []

        # Group duplicates into clusters
        clusters = self._cluster_duplicates(duplicates)

        for cluster in clusters:
            # Find best bullet to keep (highest helpful_count)
            cluster_bullets = [bullets_by_id.get(bid) for bid in cluster]
            cluster_bullets = [b for b in cluster_bullets if b is not None]

            if len(cluster_bullets) < 2:
                continue

            # Sort by helpful_count descending
            cluster_bullets.sort(
                key=lambda b: b.get('helpful_count', 0) - b.get('harmful_count', 0),
                reverse=True
            )

            keep_bullet = cluster_bullets[0]
            merge_bullets = cluster_bullets[1:]

            # Merge content (combine unique information)
            merged_content = self._merge_content([keep_bullet] + merge_bullets)

            merges.append({
                'keep_id': keep_bullet['id'],
                'merge_ids': [b['id'] for b in merge_bullets],
                'rationale': (
                    f"Merging {len(merge_bullets)} duplicate bullet(s) into {keep_bullet['id']}. "
                    f"Keep bullet has highest helpful_count ({keep_bullet.get('helpful_count', 0)}). "
                    f"Similarity scores: {[d[2] for d in duplicates if keep_bullet['id'] in d[:2]][:3]}"
                ),
                'merged_content': merged_content
            })

        return merges

    def _cluster_duplicates(
        self,
        duplicates: List[Tuple[str, str, float]]
    ) -> List[List[str]]:
        """
        Cluster duplicate pairs into groups.

        Example:
        Input: [(A, B, 0.9), (B, C, 0.85), (D, E, 0.9)]
        Output: [[A, B, C], [D, E]]
        """
        # Build adjacency map
        graph = {}
        for id1, id2, _ in duplicates:
            graph.setdefault(id1, set()).add(id2)
            graph.setdefault(id2, set()).add(id1)

        # Find connected components
        visited = set()
        clusters = []

        def dfs(node):
            component = [node]
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    component.extend(dfs(neighbor))
            return component

        for node in graph:
            if node not in visited:
                cluster = dfs(node)
                if len(cluster) > 1:
                    clusters.append(cluster)

        return clusters

    def _merge_content(self, bullets: List[Dict]) -> str:
        """
        Merge content from multiple bullets.

        Strategy: Combine unique sentences, prefer content from bullet with
        highest helpful_count.
        """
        if not bullets:
            return ""

        # Sort by helpful_count
        bullets_sorted = sorted(
            bullets,
            key=lambda b: b.get('helpful_count', 0),
            reverse=True
        )

        # Start with highest-rated content
        base_content = bullets_sorted[0].get('content', '')

        # Add unique sentences from other bullets
        base_sentences = set(s.strip() for s in base_content.split('.') if s.strip())

        for bullet in bullets_sorted[1:]:
            content = bullet.get('content', '')
            for sentence in content.split('.'):
                sentence = sentence.strip()
                if sentence and sentence not in base_sentences:
                    base_content += f" {sentence}."
                    base_sentences.add(sentence)

        return base_content
