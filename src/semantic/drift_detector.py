from dataclasses import dataclass
from enum import Enum
from collections import deque
import time
import numpy as np

class FocusState(Enum):
    FOCUSED = "focused"
    POTENTIAL_DRIFT = "potential_drift"
    DISTRACTED = "distracted"

@dataclass
class ActivityAssessment:
    activity: str
    similarity: float
    state: FocusState
    duration_seconds: float
    recent_distraction_ratio: float
    switch_count: int
    intervention_required: bool

@dataclass
class ActivityRecord:
    activity: str
    similarity: float
    duration_seconds: float
    relevant: bool
    timestamp: float

class DriftDetector:
    def __init__(
        self,
        focused_threshold=0.22,
        potential_threshold=0.15,
        drift_seconds=45.0,
        history_seconds=180.0,
        min_distraction_episode_seconds=20.0,
        repeated_distraction_seconds=60.0,
        repeated_distraction_episodes=2,
    ):
        self.focused_threshold = focused_threshold
        self.potential_threshold = potential_threshold
        self.drift_seconds = drift_seconds
        self.history_seconds = history_seconds
        self.min_distraction_episode_seconds = min_distraction_episode_seconds
        self.repeated_distraction_seconds = repeated_distraction_seconds
        self.repeated_distraction_episodes = repeated_distraction_episodes

        self.history = deque()
        self.last_activity = None
        self.switch_count = 0
        self.intervention_active = False

    def similarity(self, goal_embedding, activity_embedding):
        return float(np.dot(goal_embedding, activity_embedding))

    def _prune_history(self, now):
        cutoff = now - self.history_seconds
        while self.history and self.history[0].timestamp < cutoff:
            self.history.popleft()

    def _record_activity(self, activity, similarity, duration, relevant, now):
        if self.last_activity != activity:
            if self.last_activity is not None:
                self.switch_count += 1
            self.last_activity = activity

        if self.history and self.history[-1].activity == activity:
            self.history[-1].duration_seconds = duration
            self.history[-1].similarity = similarity
            self.history[-1].relevant = relevant
            self.history[-1].timestamp = now
            return

        self.history.append(
            ActivityRecord(
                activity=activity,
                similarity=similarity,
                duration_seconds=duration,
                relevant=relevant,
                timestamp=now,
            )
        )

    def _real_distraction_records(self):
        return [
            record
            for record in self.history
            if not record.relevant
            and record.duration_seconds >= self.min_distraction_episode_seconds
        ]

    def _recent_distraction_seconds(self):
        return sum(
            record.duration_seconds
            for record in self._real_distraction_records()
        )

    def _recent_total_seconds(self):
        return sum(
            record.duration_seconds
            for record in self.history
            if record.relevant
            or record.duration_seconds >= self.min_distraction_episode_seconds
        )

    def _distraction_ratio(self):
        total = self._recent_total_seconds()
        if total <= 0:
            return 0.0
        return self._recent_distraction_seconds() / total

    def _distraction_episode_count(self):
        return len(self._real_distraction_records())

    def assess(self, goal_embedding, activity_embedding, activity, duration_seconds):
        now = time.time()
        score = self.similarity(goal_embedding, activity_embedding)

        if score >= self.focused_threshold:
            relevant = True
            current_state = FocusState.FOCUSED
        else:
            relevant = False
            current_state = FocusState.POTENTIAL_DRIFT

        self._record_activity(
            activity,
            score,
            duration_seconds,
            relevant,
            now,
        )
        self._prune_history(now)

        distraction_seconds = self._recent_distraction_seconds()
        distraction_ratio = self._distraction_ratio()
        distraction_episodes = self._distraction_episode_count()

        sustained_drift = (
            not relevant
            and duration_seconds >= self.drift_seconds
        )

        repeated_drift = (
            not relevant
            and distraction_episodes >= self.repeated_distraction_episodes
            and distraction_seconds >= self.repeated_distraction_seconds
        )

        intervention_required = (
            sustained_drift or repeated_drift
        ) and not self.intervention_active

        if relevant:
            self.intervention_active = False
            current_state = FocusState.FOCUSED
        elif intervention_required:
            self.intervention_active = True
            current_state = FocusState.DISTRACTED

        return ActivityAssessment(
            activity=activity,
            similarity=score,
            state=current_state,
            duration_seconds=duration_seconds,
            recent_distraction_ratio=distraction_ratio,
            switch_count=self.switch_count,
            intervention_required=intervention_required,
        )