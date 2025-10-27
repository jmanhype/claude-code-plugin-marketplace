"""
FAISS-based semantic deduplication for ACE Curator.

Uses FAISS (Facebook AI Similarity Search) with sentence embeddings
for efficient semantic similarity search, as described in ACE paper Section 3.2.
"""

import numpy as np
from typing import List, Dict, Tuple
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class FAISSDeduplicator:
    """
    Semantic deduplication using FAISS and sentence embeddings.

    Implements grow-and-refine mechanism from ACE paper (Section 3.2):
    - Compares bullets via semantic embeddings (not TF-IDF)
    - Uses FAISS for efficient similarity search
    - Finds duplicates above threshold
    - Proposes merge operations
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Args:
            model_name: Sentence transformer model for embeddings
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS and sentence-transformers required for semantic deduplication. "
                "Install with: pip install faiss-cpu sentence-transformers"
            )

        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✓ Initialized FAISS deduplicator with {model_name} (dim={self.embedding_dim})")

    def find_duplicates(
        self,
        bullets: List[Dict],
        threshold: float = 0.85
    ) -> List[Tuple[str, str, float]]:
        """
        Find duplicate bullets using FAISS semantic similarity.

        Args:
            bullets: List of bullet dictionaries with 'id', 'title', 'content'
            threshold: Cosine similarity threshold (0.85 = 85% similar)

        Returns:
            List of (bullet_id_1, bullet_id_2, similarity_score) tuples
        """
        # Filter active bullets
        active_bullets = [b for b in bullets if b.get('status') == 'active']

        if len(active_bullets) < 2:
            return []

        # Create text representations
        texts = []
        bullet_ids = []
        for b in active_bullets:
            text = f"{b.get('title', '')} {b.get('content', '')}"
            texts.append(text)
            bullet_ids.append(b['id'])

        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        embeddings = embeddings.astype('float32')

        # Build FAISS index (using inner product for normalized vectors = cosine similarity)
        index = faiss.IndexFlatIP(self.embedding_dim)
        index.add(embeddings)

        # Search for similar bullets
        # For each bullet, find all others with similarity >= threshold
        duplicates = []

        for i, query_embedding in enumerate(embeddings):
            # Search for top-k similar bullets
            # k = min(len(embeddings), 100) to avoid searching entire corpus
            k = min(len(embeddings), 100)
            distances, indices = index.search(query_embedding.reshape(1, -1), k)

            for j, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                # Skip self-matches and pairs already seen
                if idx <= i:
                    continue

                similarity = float(dist)  # Already cosine sim due to normalized embeddings

                if similarity >= threshold:
                    duplicates.append((
                        bullet_ids[i],
                        bullet_ids[idx],
                        similarity
                    ))

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def propose_merges(
        self,
        bullets: List[Dict],
        duplicates: List[Tuple[str, str, float]]
    ) -> List[Dict]:
        """
        Propose merge operations for duplicate bullets.

        Strategy:
        - Keep bullet with higher helpful_count
        - Merge content preserving unique information
        - Archive duplicates

        Returns:
            List of merge operations:
            [{
                'keep_id': 'bullet-123',
                'merge_ids': ['bullet-456'],
                'rationale': '...',
                'merged_content': '...',
                'similarity_scores': [0.92, 0.89]
            }, ...]
        """
        bullets_by_id = {b['id']: b for b in bullets}
        merges = []

        # Cluster duplicates into connected components
        clusters = self._cluster_duplicates(duplicates)

        for cluster in clusters:
            # Get bullets in cluster
            cluster_bullets = [bullets_by_id.get(bid) for bid in cluster]
            cluster_bullets = [b for b in cluster_bullets if b is not None]

            if len(cluster_bullets) < 2:
                continue

            # Sort by helpfulness (helpful_count - harmful_count)
            cluster_bullets.sort(
                key=lambda b: b.get('helpful_count', 0) - b.get('harmful_count', 0),
                reverse=True
            )

            keep_bullet = cluster_bullets[0]
            merge_bullets = cluster_bullets[1:]

            # Get similarity scores for this cluster
            cluster_sims = [
                d[2] for d in duplicates
                if (d[0] in cluster and d[1] in cluster)
            ]

            # Merge content
            merged_content = self._merge_content([keep_bullet] + merge_bullets)

            merges.append({
                'keep_id': keep_bullet['id'],
                'merge_ids': [b['id'] for b in merge_bullets],
                'rationale': (
                    f"Merging {len(merge_bullets)} semantically duplicate bullet(s) into {keep_bullet['id']}. "
                    f"Keep bullet has highest net helpful count "
                    f"({keep_bullet.get('helpful_count', 0) - keep_bullet.get('harmful_count', 0)}). "
                    f"FAISS similarity scores: {cluster_sims[:3]}"
                ),
                'merged_content': merged_content,
                'similarity_scores': cluster_sims
            })

        return merges

    def _cluster_duplicates(
        self,
        duplicates: List[Tuple[str, str, float]]
    ) -> List[List[str]]:
        """
        Cluster duplicate pairs into connected components.

        Example:
        Input: [(A, B, 0.9), (B, C, 0.85), (D, E, 0.9)]
        Output: [[A, B, C], [D, E]]
        """
        # Build adjacency graph
        graph = {}
        for id1, id2, _ in duplicates:
            graph.setdefault(id1, set()).add(id2)
            graph.setdefault(id2, set()).add(id1)

        # Find connected components via DFS
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
        Merge content from multiple bullets, preserving unique information.

        Strategy:
        - Start with highest-rated bullet's content
        - Add unique sentences from other bullets
        - Prefer content from bullets with higher helpful_count
        """
        if not bullets:
            return ""

        # Sort by helpful_count descending
        bullets_sorted = sorted(
            bullets,
            key=lambda b: b.get('helpful_count', 0) - b.get('harmful_count', 0),
            reverse=True
        )

        # Start with best content
        base_content = bullets_sorted[0].get('content', '')
        base_sentences = set(s.strip() for s in base_content.split('.') if s.strip())

        # Add unique sentences from other bullets
        for bullet in bullets_sorted[1:]:
            content = bullet.get('content', '')
            for sentence in content.split('.'):
                sentence = sentence.strip()
                if sentence and sentence not in base_sentences:
                    base_content += f" {sentence}."
                    base_sentences.add(sentence)

        return base_content.strip()
