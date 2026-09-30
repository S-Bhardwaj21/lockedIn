import re
from dataclasses import dataclass

STOPWORDS = {
    "a", "an", "the", "my", "me", "for", "to", "of", "on", "in",
    "and", "or", "with", "from", "this", "that", "is", "are", "do",
    "i", "want", "need", "find", "watch", "finish", "make", "build",
    "good", "new", "best", "latest", "2026",
}

COMPOUND_TERMS = {
    "cdrama": "chinese drama",
    "cdramas": "chinese drama",
    "kdrama": "korean drama",
    "kdramas": "korean drama",
    "ml": "machine learning",
    "stackoverflow": "stack overflow",
    "github": "git hub",
}

@dataclass
class AlignmentResult:
    semantic_similarity: float
    lexical_overlap: float
    combined_score: float
    matched_terms: list[str]
    decision: str

class AlignmentEngine:
    def __init__(
        self,
        semantic_weight=0.75,
        lexical_weight=0.25,
        relevant_threshold=0.30,
        uncertain_threshold=0.20,
        strong_semantic_threshold=0.45,
    ):
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        self.relevant_threshold = relevant_threshold
        self.uncertain_threshold = uncertain_threshold
        self.strong_semantic_threshold = strong_semantic_threshold

    def _normalize(self, text):
        text = text.lower()

        for source, replacement in COMPOUND_TERMS.items():
            text = re.sub(
                rf"\b{re.escape(source)}\b",
                replacement,
                text,
            )

        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _tokens(self, text):
        normalized = self._normalize(text)
        tokens = normalized.split()

        return {
            token
            for token in tokens
            if token not in STOPWORDS and len(token) > 1
        }

    def lexical_overlap(self, goal, activity):
        goal_tokens = self._tokens(goal)
        activity_tokens = self._tokens(activity)

        if not goal_tokens or not activity_tokens:
            return 0.0, []

        matched = sorted(goal_tokens & activity_tokens)
        score = len(matched) / len(goal_tokens)

        return score, matched

    def compare(
        self,
        goal,
        activity,
        goal_embedding,
        activity_embedding,
    ):
        semantic = float(goal_embedding @ activity_embedding)
        lexical, matched_terms = self.lexical_overlap(
            goal,
            activity,
        )

        if semantic >= self.strong_semantic_threshold:
            combined = semantic
        elif lexical > 0:
            combined = (
                self.semantic_weight * semantic
                + self.lexical_weight * lexical
            )
        else:
            combined = semantic

        if combined >= self.relevant_threshold:
            decision = "relevant"
        elif combined >= self.uncertain_threshold:
            decision = "uncertain"
        else:
            decision = "unrelated"

        return AlignmentResult(
            semantic_similarity=semantic,
            lexical_overlap=lexical,
            combined_score=combined,
            matched_terms=matched_terms,
            decision=decision,
        )