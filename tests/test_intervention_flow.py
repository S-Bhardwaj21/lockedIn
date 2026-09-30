import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior.focus_state_machine import FocusStateMachine, BehaviorState
from ui.intervention_popup import InterventionPopup


def main():
    app = QApplication(sys.argv)
    machine = FocusStateMachine()

    print("LOCKEDIN intervention flow test")
    print("-" * 40)

    timeline = [
        (0, True, "VS Code"),
        (5, False, "YouTube"),
        (15, False, "YouTube"),
        (25, False, "YouTube"),
        (35, False, "YouTube"),
        (45, False, "YouTube"),
        (50, False, "YouTube"),
    ]

    print("\nSimulating focus timeline...")

    intervention = False

    for now, relevant, activity in timeline:
        result = machine.update(
            relevant=relevant,
            activity=activity,
            now=now,
        )

        print(
            f"{now:>3}s | "
            f"{activity:<10} | "
            f"{result.state.value:<16} | "
            f"indicator={result.show_indicator} | "
            f"intervention={result.trigger_intervention}"
        )

        if result.trigger_intervention:
            intervention = True
            break

    if not intervention:
        print("\nERROR: Intervention did not trigger.")
        return

    print("\nIntervention triggered successfully.")

    popup = InterventionPopup(
        "Finish my machine learning assignment"
    )

    def working():
        decision = machine.acknowledge_working(now=50)
        print("\nUSER ACTION: I'm working")
        print("State:", decision.state.value)
        print("Expected: cooldown")

    def take_break():
        decision = machine.take_break(now=50)
        print("\nUSER ACTION: Taking a break")
        print("State:", decision.state.value)
        print("Expected: break")

    def take_me_back():
        decision = machine.take_me_back(now=50)
        print("\nUSER ACTION: Take me back")
        print("State:", decision.state.value)
        print("Expected: focused")

    popup.working_clicked.connect(working)
    popup.break_clicked.connect(take_break)
    popup.take_me_back_clicked.connect(take_me_back)

    print("\nShowing intervention popup...")
    popup.show_popup()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()