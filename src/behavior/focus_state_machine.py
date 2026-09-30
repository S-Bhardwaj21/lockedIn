from dataclasses import dataclass
from enum import Enum
import time

class BehaviorState(Enum):
    FOCUSED = "focused"
    POTENTIAL_DRIFT = "potential_drift"
    CONFIRMING = "confirming"
    INTERVENTION = "intervention"
    COOLDOWN = "cooldown"
    BREAK = "break"

@dataclass
class BehaviorDecision:
    state: BehaviorState
    show_indicator: bool = False
    trigger_intervention: bool = False
    reset_history: bool = False
    reason: str = ""

class FocusStateMachine:
    def __init__(
        self,
        unrelated_start_seconds=20.0,
        confirming_seconds=45.0,
        cumulative_seconds=60.0,
        history_seconds=180.0,
        recovery_seconds=10.0,
        cooldown_seconds=90.0,
        break_seconds=600.0,
    ):
        self.unrelated_start_seconds = unrelated_start_seconds
        self.confirming_seconds = confirming_seconds
        self.cumulative_seconds = cumulative_seconds
        self.history_seconds = history_seconds
        self.recovery_seconds = recovery_seconds
        self.cooldown_seconds = cooldown_seconds
        self.break_seconds = break_seconds

        self.state = BehaviorState.FOCUSED
        self.current_relevant = None
        self.current_activity = None
        self.relevant_started = None
        self.distraction_started = None
        self.distraction_episodes = []
        self.cooldown_until = 0.0
        self.break_until = 0.0
        self.acknowledged_activity = None

    def _now(self):
        return time.monotonic()

    def _prune_history(self, now):
        cutoff = now - self.history_seconds
        self.distraction_episodes = [
            episode
            for episode in self.distraction_episodes
            if episode["ended_at"] >= cutoff
        ]

    def _start_distraction(self, now):
        if self.distraction_started is None:
            self.distraction_started = now

    def _end_distraction(self, now):
        if self.distraction_started is None:
            return

        duration = now - self.distraction_started

        if duration >= self.unrelated_start_seconds:
            self.distraction_episodes.append(
                {
                    "started_at": self.distraction_started,
                    "ended_at": now,
                    "duration": duration,
                }
            )

        self.distraction_started = None

    def _distraction_duration(self, now):
        if self.distraction_started is None:
            return 0.0
        return now - self.distraction_started

    def _episode_count(self, now):
        self._prune_history(now)

        count = len(self.distraction_episodes)

        if (
            self.distraction_started is not None
            and self._distraction_duration(now)
            >= self.unrelated_start_seconds
        ):
            count += 1

        return count

    def _cumulative_distraction(self, now):
        self._prune_history(now)

        total = sum(
            episode["duration"]
            for episode in self.distraction_episodes
        )

        if (
            self.distraction_started is not None
            and self._distraction_duration(now)
            >= self.unrelated_start_seconds
        ):
            total += self._distraction_duration(now)

        return total

    def _reset_distraction_history(self):
        self.distraction_started = None
        self.distraction_episodes.clear()

    def update(self, relevant, activity=None, now=None):
        if now is None:
            now = self._now()

        activity_changed = (
            activity != self.current_activity
        )

        if activity_changed:
            self.acknowledged_activity = None
            self.current_activity = activity

        if self.state == BehaviorState.BREAK:
            if now < self.break_until:
                return BehaviorDecision(
                    state=self.state,
                    reason="Break mode active.",
                )

            self.state = BehaviorState.FOCUSED
            self._reset_distraction_history()

        if relevant:
            self.acknowledged_activity = None

            if self.current_relevant is not True:
                self.relevant_started = now

            self.current_relevant = True

            if self.relevant_started is not None:
                relevant_duration = (
                    now - self.relevant_started
                )

                if relevant_duration > self.recovery_seconds:
                    self._end_distraction(now)
                    self._reset_distraction_history()
                    self.state = BehaviorState.FOCUSED

                    return BehaviorDecision(
                        state=self.state,
                        reset_history=True,
                        reason=(
                            "Relevant activity stable "
                            "for recovery window."
                        ),
                    )

            self.state = BehaviorState.FOCUSED

            return BehaviorDecision(
                state=self.state,
                reason="Relevant activity.",
            )

        self.current_relevant = False
        self.relevant_started = None

        if (
            self.acknowledged_activity is not None
            and activity == self.acknowledged_activity
        ):
            self.state = BehaviorState.COOLDOWN

            return BehaviorDecision(
                state=self.state,
                reason=(
                    "User explicitly acknowledged "
                    "this activity."
                ),
            )

        if self.state == BehaviorState.COOLDOWN:
            if now < self.cooldown_until:
                return BehaviorDecision(
                    state=self.state,
                    reason="User override cooldown active.",
                )

            self.state = BehaviorState.FOCUSED
            self._reset_distraction_history()

        self._start_distraction(now)

        duration = self._distraction_duration(now)

        if duration < self.unrelated_start_seconds:
            self.state = BehaviorState.FOCUSED

            return BehaviorDecision(
                state=self.state,
                reason=(
                    "Unrelated activity has not "
                    "lasted 20 seconds."
                ),
            )

        if duration < self.confirming_seconds:
            self.state = BehaviorState.POTENTIAL_DRIFT

            return BehaviorDecision(
                state=self.state,
                show_indicator=True,
                reason="Potential distraction.",
            )

        self.state = BehaviorState.CONFIRMING

        cumulative = self._cumulative_distraction(now)
        episodes = self._episode_count(now)

        continuous_ready = (
            duration >= self.confirming_seconds
        )

        repeated_ready = (
            episodes >= 2
            and cumulative >= self.cumulative_seconds
        )

        if continuous_ready or repeated_ready:
            self.state = BehaviorState.INTERVENTION

            reason = (
                "Continuous distraction exceeded 45 seconds."
                if continuous_ready
                else (
                    "Repeated distraction exceeded "
                    "60 seconds in 3 minutes."
                )
            )

            return BehaviorDecision(
                state=self.state,
                trigger_intervention=True,
                reason=reason,
            )

        return BehaviorDecision(
            state=self.state,
            show_indicator=True,
            reason="Distraction threshold not yet reached.",
        )

    def acknowledge_working(self, now=None):
        if now is None:
            now = self._now()

        self._end_distraction(now)
        self._reset_distraction_history()

        self.acknowledged_activity = (
            self.current_activity
        )

        self.cooldown_until = (
            now + self.cooldown_seconds
        )

        self.state = BehaviorState.COOLDOWN

        return BehaviorDecision(
            state=self.state,
            reset_history=True,
            reason=(
                "User explicitly acknowledged "
                "the current activity."
            ),
        )

    def take_break(self, now=None):
        if now is None:
            now = self._now()

        self._end_distraction(now)
        self._reset_distraction_history()

        self.acknowledged_activity = None

        self.break_until = (
            now + self.break_seconds
        )

        self.state = BehaviorState.BREAK

        return BehaviorDecision(
            state=self.state,
            reset_history=True,
            reason="User started a break.",
        )

    def take_me_back(self, now=None):
        if now is None:
            now = self._now()

        self._end_distraction(now)
        self._reset_distraction_history()

        self.acknowledged_activity = None
        self.current_activity = None

        self.state = BehaviorState.FOCUSED

        return BehaviorDecision(
            state=self.state,
            reset_history=True,
            reason="User requested workspace recovery.",
        )

    def reset_history(self):
        self._reset_distraction_history()
        self.relevant_started = None