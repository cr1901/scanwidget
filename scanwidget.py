from PyQt5 import QtGui, QtCore, QtWidgets

# ScanAxis consists of a horizontal line extending indefinitely, major and
# minor ticks, and numbers over the major ticks. During a redraw, the width
# between adjacent ticks is recalculated, based on the new requested bounds.
#
# If the width is smaller than a certain threshold, the major ticks become
# minor ticks, and the minor ticks are deleted as objects.
class ScanAxis(QtWidgets.QGraphicsWidget):
    def __init__(self):
        QtWidgets.QGraphicsWidget.__init__(self)
        self.boundleft = 0
        self.boundright = 1

    def paint(self, painter, op, widget):
        pass

# ScanScene holds all the objects.
class ScanScene(QtWidgets.QGraphicsScene):
    def __init__(self):
        QtWidgets.QGraphicsScene.__init__(self)


    # def mouseClickEvent(self, ev):
    #     pass
    # 
    # def mouseDragEvent(self, ev):
    #     pass
    # 
    # def keyPressEvent(self, ev):

# Check for mouse events over the widget. If shift pressed and mouse click,
# change signal/event propogation to alter the number of points over which
# to scan.
class ScanBox(QtWidgets.QWidget):
    pass

# The ScanWidget proper 
class ScanWidget(QtWidgets.QGraphicsView):
    def __init__(self):
        self.scene = ScanScene()
        QtWidgets.QGraphicsView.__init__(self, self.scene)
