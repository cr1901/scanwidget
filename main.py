import asyncio
import atexit
import scanwidget

from quamash import QApplication, QEventLoop, QtCore, QtWidgets


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, app, server):
        QtWidgets.QMainWindow.__init__(self)
        self.exit_request = asyncio.Event()

    def closeEvent(self, *args):
        self.exit_request.set()

    def save_state(self):
        return bytes(self.saveGeometry())

    def restore_state(self, state):
        self.restoreGeometry(QtCore.QByteArray(state))


def main():
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    atexit.register(loop.close)

    win = MainWindow(app, None)

    container = QtWidgets.QWidget(win)
    layout = QtWidgets.QGridLayout()
    container.setLayout(layout)
    scanner = scanwidget.ScanWidget()
    layout.addWidget(scanner, 0, 0, 1, -1)

    spinboxes = [QtWidgets.QDoubleSpinBox(), QtWidgets.QDoubleSpinBox(),
                 QtWidgets.QSpinBox()]
    for s in spinboxes:
        if type(s) is QtWidgets.QDoubleSpinBox:
            s.setDecimals(13)
            s.setMaximum(float("Inf"))
            s.setMinimum(float("-Inf"))
        else:
            s.setMinimum(1)
            s.setValue(10)

    for (col, w) in enumerate([QtWidgets.QLabel("Start"), spinboxes[0],
                               QtWidgets.QLabel("Stop"), spinboxes[1],
                               QtWidgets.QLabel("Points"), spinboxes[2]]):
        layout.addWidget(w, 1, col)

    scanner.sigMinMoved.connect(spinboxes[0].setValue)
    scanner.sigMaxMoved.connect(spinboxes[1].setValue)
    # scanner.sigNumChanged.connect(spinboxes[2].setValue)
    spinboxes[0].valueChanged.connect(scanner.setMin)
    spinboxes[1].valueChanged.connect(scanner.setMax)
    # spinboxes[2].valueChanged.connect(scanner.setNumPoints)

    win.setCentralWidget(container)
    win.show()
    scanner.fitToView()
    loop.run_until_complete(win.exit_request.wait())


if __name__ == "__main__":
    main()
