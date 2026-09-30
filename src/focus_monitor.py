import signal
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from semantic.embedder import MiniLMEmbedder
from semantic.alignment import AlignmentEngine
from behavior.focus_state_machine import FocusStateMachine
from behavior.activity_session import ActivitySessionTracker
from context.windows_context import WindowsContextObserver
from context.browser_context import BrowserContextProvider
from context.context_normalizer import ContextNormalizer
from ui.intervention_popup import InterventionPopup
from workspace_recovery import WorkspaceRecovery
from voice import VoicePersonality


class LockedInTray:
    def __init__(self, monitor):
        self.monitor = monitor
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self._create_icon())
        self.tray.setToolTip(f"LOCKEDIN — {monitor.goal_text}")

        menu = QMenu()

        goal_action = QAction(f"Goal: {monitor.goal_text}", menu)
        goal_action.setEnabled(False)

        status_action = QAction("● LOCKED IN", menu)
        status_action.setEnabled(False)

        menu.addAction(goal_action)
        menu.addSeparator()
        menu.addAction(status_action)
        menu.addSeparator()

        done_action = QAction("I'm done", menu)
        done_action.triggered.connect(monitor.on_done)
        menu.addAction(done_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

        self.menu = menu
        self.status_action = status_action

        self.tray.show()
        print(">>> LOCKEDIN tray control ready.")

    def _create_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRoundedRect(2, 2, 28, 28, 8, 8)
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "L",
        )
        painter.end()

        return QIcon(pixmap)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.tray.showMessage(
                "LOCKEDIN",
                "Right-click the tray icon for controls.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )

    def update_status(self, text):
        self.status_action.setText(text)

    def close(self):
        self.tray.hide()


class LockedInMonitor:
    def __init__(self, goal_text):
        self.goal_text = goal_text
        self.session_active = True

        self.embedder = MiniLMEmbedder()
        self.alignment = AlignmentEngine()
        self.behavior = FocusStateMachine()
        self.sessions = ActivitySessionTracker()
        self.observer = WindowsContextObserver()
        self.browser = BrowserContextProvider()
        self.normalizer = ContextNormalizer()
        self.workspace = WorkspaceRecovery()
        self.voice = VoicePersonality()

        self.goal_embedding = self.embedder.embed(goal_text)

        self.current_context = None
        self.current_embedding = None
        self.popup = None
        self.tray = None

        self.last_logged_activity = None
        self.last_logged_state = None

        self.workspace_candidate = None
        self.workspace_candidate_started = None
        self.workspace_candidate_window = None
        self.workspace_candidate_browser = None
        self.workspace_captured_for_activity = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(2000)

        print(f"\nGoal locked: {goal_text}")
        print("LOCKEDIN is watching.")
        print("Use the LOCKEDIN tray icon to end the session.\n")

    def attach_tray(self):
        self.tray = LockedInTray(self)

    def _clear_workspace_candidate(self):
        self.workspace_candidate = None
        self.workspace_candidate_started = None
        self.workspace_candidate_window = None
        self.workspace_candidate_browser = None
        self.workspace_captured_for_activity = None

    def _reset_activity_tracking(self):
        self.sessions.reset()
        self.current_context = None
        self.current_embedding = None
        self.last_logged_activity = None
        self.last_logged_state = None
        self._clear_workspace_candidate()

    def _update_task_destination(
        self,
        activity,
        relevant,
        session_started_at,
        now,
        window,
        browser_context,
    ):
        if not relevant:
            self._clear_workspace_candidate()
            return

        if activity != self.workspace_candidate:
            self.workspace_candidate = activity
            self.workspace_candidate_started = session_started_at
            self.workspace_candidate_window = window
            self.workspace_candidate_browser = browser_context
            self.workspace_captured_for_activity = None

        if self.workspace_captured_for_activity == activity:
            return

        if self.workspace_candidate_started is None:
            self.workspace_candidate_started = session_started_at

        duration = now - self.workspace_candidate_started

        if duration <= 10.0:
            return

        destination_window = self.workspace_candidate_window
        destination_browser = self.workspace_candidate_browser

        if destination_window is None:
            return

        captured = False

        if destination_browser and destination_browser.url:
            captured = self.workspace.capture_browser_destination(
                destination_window,
                destination_browser.url,
                destination_browser.title,
            )
        elif destination_window.process.lower() == "code.exe":
            captured = self.workspace.capture_vscode_destination(
                destination_window.hwnd
            )
        else:
            captured = self.workspace.capture_window_destination(
                destination_window
            )

        if captured:
            self.workspace_captured_for_activity = activity
            print(f">>> Task destination locked: {activity[:100]}")

    def _log_meaningful_change(
        self,
        activity,
        alignment,
        decision,
        session_duration,
    ):
        state = decision.state.value

        activity_changed = activity != self.last_logged_activity
        state_changed = state != self.last_logged_state

        if activity_changed or state_changed:
            print(f">>> Activity: {activity[:100]}")
            print(
                f"    alignment={alignment.decision} "
                f"score={alignment.combined_score:.4f} "
                f"behavior={state} "
                f"duration={session_duration:.0f}s"
            )

            self.last_logged_activity = activity
            self.last_logged_state = state

    def tick(self):
        if not self.session_active:
            return

        window = self.observer.get_active_window()

        if window is None:
            return

        browser_context = self.browser.get_context(window)

        if browser_context:
            context_string = self.normalizer.normalize(
                window.process,
                browser_context.title,
                browser_context.url,
            )
        else:
            context_string = self.normalizer.normalize(
                window.process,
                window.title,
            )

        if not context_string:
            return

        now = time.monotonic()

        session, session_changed = self.sessions.update(
            context_string,
            now=now,
        )

        if session.activity != self.current_context:
            self.current_context = session.activity
            self.current_embedding = self.embedder.embed(
                session.activity
            )

        if self.current_embedding is None:
            return

        session_duration = now - session.started_at

        alignment = self.alignment.compare(
            self.goal_text,
            session.activity,
            self.goal_embedding,
            self.current_embedding,
        )

        relevant = alignment.decision == "relevant"

        self._update_task_destination(
            activity=session.activity,
            relevant=relevant,
            session_started_at=session.started_at,
            now=now,
            window=window,
            browser_context=browser_context,
        )

        decision = self.behavior.update(
    relevant=relevant,
    activity=session.activity,
    now=now,
)

        self._log_meaningful_change(
            activity=session.activity,
            alignment=alignment,
            decision=decision,
            session_duration=session_duration,
        )

        if self.tray:
            self.tray.update_status(
                f"● {decision.state.value.upper()}"
            )

        if decision.trigger_intervention:
            self.show_intervention()

    def show_intervention(self):
        if self.popup is not None and self.popup.isVisible():
            return

        print("\n>>> LOCKEDIN: INTERVENTION")

        self.voice.intervene()

        self.popup = InterventionPopup(self.goal_text)

        self.popup.working_clicked.connect(self.on_working)
        self.popup.break_clicked.connect(self.on_break)
        self.popup.take_me_back_clicked.connect(
            self.on_take_me_back
        )
        self.popup.done_clicked.connect(self.on_done)

        self.popup.show_popup()

    def on_working(self):
        decision = self.behavior.acknowledge_working()

        print(
            f">>> User response: I'm working → "
            f"{decision.state.value}"
        )
        print(">>> LOCKEDIN remains active.")

        self.popup = None

    def on_break(self):
        decision = self.behavior.take_break()

        print(
            f">>> User response: Taking a break → "
            f"{decision.state.value}"
        )
        print(">>> LOCKEDIN remains active.")

        self.popup = None

    def on_take_me_back(self):
        decision = self.behavior.take_me_back()

        print(
            f">>> User response: Take me back → "
            f"{decision.state.value}"
        )

        restored = self.workspace.restore()

        if restored:
            time.sleep(0.5)

            restored_window = self.observer.get_active_window()

            if restored_window is not None:
                print(
                    f">>> Foreground after restore: "
                    f"{restored_window.process} | "
                    f"{restored_window.title[:100]}"
                )

            self._reset_activity_tracking()

            print(">>> LOCKEDIN remains active.")
        else:
            print(">>> WARNING: Destination restore failed.")
            print(">>> LOCKEDIN remains active.")

        self.popup = None

    def on_done(self):
        if not self.session_active:
            return

        print("\n>>> User response: I'm done")
        print(">>> LOCKEDIN session ended.")

        self.session_active = False
        self.timer.stop()
        self.voice.stop()

        if self.popup is not None:
            self.popup.close()
            self.popup = None

        if self.tray is not None:
            self.tray.close()
            self.tray = None

        QApplication.quit()

    def stop(self):
        if not self.session_active:
            return

        print("\n>>> LOCKEDIN stopped by user.")

        self.session_active = False
        self.timer.stop()
        self.voice.stop()

        if self.popup is not None:
            self.popup.close()
            self.popup = None

        if self.tray is not None:
            self.tray.close()
            self.tray = None


def main():
    goal = input(
        "LOCKEDIN — What are you trying to accomplish?\n> "
    ).strip()

    if not goal:
        print("No goal entered.")
        return

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    keep_alive = QWidget()
    keep_alive.setAttribute(
        Qt.WidgetAttribute.WA_DontShowOnScreen,
        True,
    )
    keep_alive.setWindowTitle(
        "LOCKEDIN Background Monitor"
    )
    keep_alive.hide()

    monitor = LockedInMonitor(goal)
    monitor.attach_tray()

    def handle_sigint(signum, frame):
        monitor.stop()
        app.quit()

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        monitor.stop()
        app.quit()


if __name__ == "__main__":
    main()