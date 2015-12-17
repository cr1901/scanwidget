import asyncio
import atexit
import os
import scanwidget

# First two are portable between PyQt4 and 5. Remaining are not.
from quamash import QApplication, QEventLoop, QtGui, QtCore, QtWidgets



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
    
    # Create a window
    win = MainWindow(app, None)

    container = QtWidgets.QWidget(win)
    layout = QtWidgets.QGridLayout()
    container.setLayout(layout)
    spinboxes = [QtWidgets.QDoubleSpinBox(), QtWidgets.QDoubleSpinBox(), \
        QtWidgets.QSpinBox()]
    scanner = scanwidget.ScanWidget()

    layout.addWidget(scanner, 0, 0, 1, -1)
    
    for s in spinboxes:
        if type is QtWidgets.QDoubleSpinBox:
            s.setDecimals(3)
            s.setMaximum(float("Inf"))
            s.setMinimum(float("-Inf"))
        else:
            s.setMinimum(2)
            s.setValue(10)
    
    for (col, w) in enumerate([QtWidgets.QLabel("Min"), spinboxes[0], \
        QtWidgets.QLabel("Max"), spinboxes[1], \
        QtWidgets.QLabel("Num Points"), spinboxes[2]]):
            layout.addWidget(w, 1, col)

    scanner.sigMinChanged.connect(spinboxes[0].setValue)
    scanner.sigMaxChanged.connect(spinboxes[1].setValue)
    scanner.sigNumChanged.connect(spinboxes[2].setValue)

    win.setCentralWidget(container)
    win.show()
    loop.run_until_complete(win.exit_request.wait())


if __name__ == "__main__":
    main()
