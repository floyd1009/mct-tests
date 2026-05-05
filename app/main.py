import sys

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter, QPen
from PySide6.QtNetwork import QUdpSocket
from PySide6.QtWidgets import QApplication, QWidget


class SpeedWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.speed = 0
        self.failure = False

        self.setFixedSize(128, 128)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self.socket = QUdpSocket(self)
        self.socket.bind(3000)
        self.socket.readyRead.connect(self.read_pending_datagrams)

    def read_pending_datagrams(self) -> None:
        while self.socket.hasPendingDatagrams():
            payload = bytes(self.socket.receiveDatagram().data())
            if len(payload) < 2:
                continue
            self.speed = payload[0] % 100
            self.failure = payload[1] != 0
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("black"))

        if self.failure:
            painter.fillRect(20, 20, 88, 88, QColor("red"))
            pen = QPen(QColor("black"), 10)
            painter.setPen(pen)
            painter.drawLine(QPointF(30, 30), QPointF(98, 98))
            painter.drawLine(QPointF(98, 30), QPointF(30, 98))
            return

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Consolas", 44, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.speed:02d}")


def main() -> int:
    app = QApplication(sys.argv)
    window = SpeedWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())