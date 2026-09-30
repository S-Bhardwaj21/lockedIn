from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)


class InterventionPopup(QWidget):
    working_clicked = Signal()
    break_clicked = Signal()
    take_me_back_clicked = Signal()
    done_clicked = Signal()

    def __init__(self, goal_text="", parent=None):
        super().__init__(parent)
        self.goal_text = goal_text
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("LOCKEDIN")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.setFixedSize(440, 340)

        container = QFrame()
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background: #18181b;
                border: 1px solid #3f3f46;
                border-radius: 20px;
            }
            QLabel {
                color: white;
            }
            QLabel#title {
                font-size: 28px;
                font-weight: 800;
            }
            QLabel#message {
                font-size: 17px;
                color: #d4d4d8;
            }
            QLabel#goal {
                font-size: 14px;
                color: #a1a1aa;
                padding: 10px;
                background: #27272a;
                border-radius: 10px;
            }
            QPushButton {
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                color: white;
                background: #27272a;
            }
            QPushButton:hover {
                background: #3f3f46;
            }
            QPushButton#back {
                background: #fafafa;
                color: #18181b;
            }
            QPushButton#back:hover {
                background: #e4e4e7;
            }
            QPushButton#done {
                background: #3f3f46;
                color: #a1a1aa;
            }
            QPushButton#done:hover {
                background: #52525b;
                color: white;
            }
        """)

        title = QLabel("EXCUSE ME?? 👀")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel("Was this part of the goal?")
        message.setObjectName("message")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        goal = QLabel(self.goal_text)
        goal.setObjectName("goal")
        goal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        goal.setWordWrap(True)

        working = QPushButton("I'm working")
        working.clicked.connect(self._working)

        take_break = QPushButton("Taking a break")
        take_break.clicked.connect(self._take_break)

        take_me_back = QPushButton("Take me back")
        take_me_back.setObjectName("back")
        take_me_back.clicked.connect(self._take_me_back)

        done = QPushButton("I'm done")
        done.setObjectName("done")
        done.clicked.connect(self._done)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(working)
        buttons.addWidget(take_break)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addWidget(goal)
        layout.addLayout(buttons)
        layout.addWidget(take_me_back)
        layout.addWidget(done)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

    def _working(self):
        self.working_clicked.emit()
        self.close()

    def _take_break(self):
        self.break_clicked.emit()
        self.close()

    def _take_me_back(self):
        self.take_me_back_clicked.emit()
        self.close()

    def _done(self):
        self.done_clicked.emit()
        self.close()

    def show_popup(self):
        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    popup = InterventionPopup(
        "Finish my machine learning assignment"
    )

    popup.show_popup()

    sys.exit(app.exec())