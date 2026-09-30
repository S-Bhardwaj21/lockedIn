import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior.focus_state_machine import FocusStateMachine


def show(label, decision):
    print(
        f"{label:<35} "
        f"state={decision.state.value:<16} "
        f"intervention={decision.trigger_intervention}"
    )


def main():
    machine = FocusStateMachine()

    print("LOCKEDIN behavior state machine test")
    print("-" * 80)

    # 1. Relevant work
    show(
        "0s  VS Code / relevant",
        machine.update(True, "VS Code", now=0),
    )

    # 2. Short unrelated activity: must be ignored
    show(
        "10s YouTube / unrelated",
        machine.update(False, "YouTube", now=10),
    )

    # 3. Switch to another unrelated activity.
    # This MUST start a fresh activity timer.
    show(
        "15s Netflix / unrelated",
        machine.update(False, "Netflix", now=15),
    )

    # 4. Still below 20s on Netflix
    show(
        "30s Netflix / unrelated",
        machine.update(False, "Netflix", now=30),
    )

    # 5. Netflix has now lasted 20s -> potential drift
    show(
        "35s Netflix / unrelated",
        machine.update(False, "Netflix", now=35),
    )

    # 6. 45s continuous Netflix -> intervention
    show(
        "60s Netflix / unrelated",
        machine.update(False, "Netflix", now=60),
    )

    print("\n--- Activity boundary attack ---")

    machine.reset_history()

    # 7. 10s on Bing: below 20s, should not count
    show(
        "0s  Bing / unrelated",
        machine.update(False, "Bing", now=100),
    )

    # 8. Switch to VS Code: MUST reset distraction timer
    show(
        "10s VS Code / unrelated",
        machine.update(False, "VS Code", now=110),
    )

    # 9. Only 10s in VS Code -> still below 20s
    show(
        "20s VS Code / unrelated",
        machine.update(False, "VS Code", now=120),
    )

    # 10. Only 19s in VS Code -> still no intervention
    show(
        "29s VS Code / unrelated",
        machine.update(False, "VS Code", now=129),
    )

    print("\n--- Rapid-switch attack ---")

    machine.reset_history()

    activities = [
        ("Instagram", 200),
        ("YouTube", 205),
        ("Reddit", 210),
        ("Netflix", 215),
        ("Instagram", 220),
        ("YouTube", 225),
    ]

    for activity, timestamp in activities:
        decision = machine.update(False, activity, now=timestamp)
        show(
            f"{timestamp}s {activity} / unrelated",
            decision,
        )

    print("\n--- Recovery attack ---")

    machine.reset_history()

    show(
        "300s Netflix / unrelated",
        machine.update(False, "Netflix", now=300),
    )

    show(
        "310s Netflix / unrelated",
        machine.update(False, "Netflix", now=310),
    )

    show(
        "320s VS Code / relevant",
        machine.update(True, "VS Code", now=320),
    )

    show(
        "331s VS Code / relevant",
        machine.update(True, "VS Code", now=331),
    )


if __name__ == "__main__":
    main()