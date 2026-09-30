import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior.activity_session import ActivitySessionTracker


def main():
    tracker = ActivitySessionTracker()

    print("LOCKEDIN activity session test")
    print("-" * 40)

    session, changed = tracker.update("VS Code", now=0)
    print("0s  VS Code   →", session.activity, "duration:", tracker.duration(now=0))

    session, changed = tracker.update("YouTube", now=2)
    print("2s  YouTube   →", session.activity, "duration:", tracker.duration(now=2))

    session, changed = tracker.update("VS Code", now=4)
    print("4s  VS Code   →", session.activity, "duration:", tracker.duration(now=4))

    session, changed = tracker.update("VS Code", now=10)
    print("10s VS Code   →", session.activity, "duration:", tracker.duration(now=10))

    session, changed = tracker.update("Netflix", now=11)
    print("11s Netflix   →", session.activity, "duration:", tracker.duration(now=11))

    session, changed = tracker.update("Netflix", now=17)
    print("17s Netflix   →", session.activity, "duration:", tracker.duration(now=17))


if __name__ == "__main__":
    main()