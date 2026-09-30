from dataclasses import dataclass
import time


@dataclass
class ActivitySession:
    activity: str
    started_at: float
    last_seen_at: float


class ActivitySessionTracker:
    def __init__(self, ignored_switch_seconds=5.0):
        self.ignored_switch_seconds = ignored_switch_seconds
        self.current = None
        self.pending = None

    def update(self, activity, now=None):
        if now is None:
            now = time.monotonic()

        # First observed activity becomes the current session.
        if self.current is None:
            self.current = ActivitySession(
                activity=activity,
                started_at=now,
                last_seen_at=now,
            )
            return self.current, True

        # Same activity: continue the current session.
        if activity == self.current.activity:
            self.current.last_seen_at = now
            self.pending = None
            return self.current, False

        # New activity detected.
        if self.pending is None:
            self.pending = ActivitySession(
                activity=activity,
                started_at=now,
                last_seen_at=now,
            )

            # This is only a pending switch.
            # The current session has NOT changed.
            return self.current, False

        # Same pending activity continues.
        if activity == self.pending.activity:
            self.pending.last_seen_at = now

            pending_duration = now - self.pending.started_at

            # Still too short to become the current activity.
            if pending_duration < self.ignored_switch_seconds:
                return self.current, False

            # The new activity is now stable enough to become
            # the actual current session.
            self.current = ActivitySession(
                activity=self.pending.activity,
                started_at=self.pending.started_at,
                last_seen_at=now,
            )
            self.pending = None

            return self.current, True

        # User switched again before the pending activity became
        # stable. Replace the pending candidate.
        self.pending = ActivitySession(
            activity=activity,
            started_at=now,
            last_seen_at=now,
        )

        return self.current, False

    def duration(self, now=None):
        if self.current is None:
            return 0.0

        if now is None:
            now = time.monotonic()

        return now - self.current.started_at

    def reset(self):
        self.current = None
        self.pending = None