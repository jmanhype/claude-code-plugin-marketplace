"""
Bullet retrieval using TF-IDF + tag overlap + helpfulness scoring.
Wraps the existing retrieve_bullets.py script.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Result from bullet retrieval."""
    bullet_id: str
    title: str
    score: float
    tags: List[str]
    confidence: float
    content: str = ""

    def to_dict(self) -> Dict:
        return {
            'id': self.bullet_id,
            'title': self.title,
            'score': self.score,
            'tags': self.tags,
            'confidence': self.confidence,
            'content': self.content
        }


class BulletRetriever:
    """
    Retrieves relevant bullets using:
    - TF-IDF cosine similarity
    - Tag overlap
    - Helpfulness prior (helpful_count - harmful_count)

    Formula: score = 2.0 * tag_overlap + cosine(TF-IDF) + 0.1 * log1p(helpful - harmful)
    """

    def __init__(self, playbook_path: str):
        self.playbook_path = Path(playbook_path)
        self.playbook = self._load_playbook()
        self.bullets_by_id = {b['id']: b for b in self.playbook.get('bullets', [])}

    def _load_playbook(self) -> Dict:
        """Load playbook from JSON file."""
        with open(self.playbook_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Handle both nested and flat structures
        if isinstance(data, dict) and 'bullets' in data:
            return data
        return {'bullets': data}

    def retrieve(self, query: str, tags: List[str] = None, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve top-k bullets for a query.

        Args:
            query: Task description or instruction
            tags: Optional tags to filter/boost (e.g., ['tool.edit', 'json'])
            top_k: Number of results to return

        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        # Use the existing retrieve_bullets.py script
        script_path = self.playbook_path.parent.parent / 'scripts' / 'retrieve_bullets.py'

        cmd = [
            'python3',
            str(script_path),
            str(self.playbook_path),
            query,
            '--topk', str(top_k)
        ]

        if tags:
            cmd.extend(['--tags', ','.join(tags)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            retrieval_results = json.loads(result.stdout)

            # Convert to RetrievalResult objects with full content
            results = []
            for r in retrieval_results:
                bullet = self.bullets_by_id.get(r['id'])
                if bullet:
                    results.append(RetrievalResult(
                        bullet_id=r['id'],
                        title=r['title'],
                        score=r['score'],
                        tags=r['tags'],
                        confidence=r.get('confidence', 0.5),
                        content=bullet.get('content', '')
                    ))

            return results

        except subprocess.CalledProcessError as e:
            print(f"Retrieval error: {e.stderr}")
            return []

    def retrieve_by_tags(self, tags: List[str], top_k: int = 10) -> List[RetrievalResult]:
        """
        Retrieve bullets matching specific tags.

        Args:
            tags: Tags to match (e.g., ['tool.edit', 'antipattern'])
            top_k: Maximum number to return

        Returns:
            List of matching bullets sorted by helpfulness
        """
        tag_set = set(tags)
        matching = []

        for bullet in self.playbook.get('bullets', []):
            if bullet.get('status') != 'active':
                continue

            bullet_tags = set(bullet.get('tags', []))
            overlap = len(bullet_tags & tag_set)

            if overlap > 0:
                helpful = bullet.get('helpful_count', 0)
                harmful = bullet.get('harmful_count', 0)
                score = overlap + 0.1 * max(0, helpful - harmful)

                matching.append((score, bullet))

        # Sort by score and return top-k
        matching.sort(reverse=True, key=lambda x: x[0])

        results = []
        for score, bullet in matching[:top_k]:
            results.append(RetrievalResult(
                bullet_id=bullet['id'],
                title=bullet['title'],
                score=score,
                tags=bullet.get('tags', []),
                confidence=bullet.get('confidence', 0.5),
                content=bullet.get('content', '')
            ))

        return results

    def get_bullet(self, bullet_id: str) -> Optional[Dict]:
        """Get full bullet by ID."""
        return self.bullets_by_id.get(bullet_id)

    def get_all_active_bullets(self) -> List[Dict]:
        """Get all active bullets."""
        return [b for b in self.playbook.get('bullets', [])
                if b.get('status') == 'active']
