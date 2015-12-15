import math

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


# class ScanModel(QO


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
# to scan. This widget should intercept mouse events/prevent events from
# reaching ScanSlider if shift is pressed.
class ScanBox(QtWidgets.QWidget):
    pass


# Needs to be subclassed from QGraphicsItem* b/c Qt will not send mouse events
# to GraphicsItems that do not reimplement mousePressEvent (How does Qt know?).
# Qt decides this while iterating to find which GraphicsItem should get control
# of the mouse. mousePressEvent is accepted by default.
# TODO: The slider that was most recently clicked should have z-priority.
# Qt's mouseGrab logic should implement this correctly.
# * Subclassed from QGraphicsObject to get signal functionality.
class ScanSlider(QtWidgets.QGraphicsObject):
    sigPosChanged = QtCore.Signal(object)
    
    def __init__(self, px_size = 20):
        QtWidgets.QGraphicsItem.__init__(self)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        
        # Make slider an equilateral triangle w/ sides px_size pixels wide.
        altitude = math.ceil((px_size/2)*math.sqrt(3))
        
        points = [QtCore.QPoint(-(px_size/2), altitude), QtCore.QPoint(0, 0), \
            QtCore.QPoint((px_size/2), altitude)]
        self.shape = QtGui.QPolygon(points)

    def boundingRect(self):
        pen_width = 1
        # If bounding box does not cover whole polygon, trails will be left
        # when the object is moved.
        return QtCore.QRectF(-10 - pen_width/2, 0 - pen_width / 2, \
            20 + pen_width, 20 + pen_width)

    def paint(self, painter, op, widget):
        painter.drawConvexPolygon(self.shape)

    def mousePressEvent(self, ev):
        QtWidgets.QGraphicsItem.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):
        QtWidgets.QGraphicsItem.mouseMoveEvent(self, ev)
        self.sigPosChanged.emit(self.scenePos().x())
        

# Is it scene's responsibility or item's responsibility to ensure item stays
# in range of allowed moves?
    def itemChange(self, change, val):
        # if change == QtWidgets.QGraphicsItem.ItemPositionChange:
        #     print("Position changed")
        # else:
        #     print(change)

        return QtWidgets.QGraphicsItem.itemChange(self, change, val)

# The ScanWidget proper.
# TODO: Scene is centered on visible items by default when the scene is first
# viewed. We do not want this here; viewed portion of scene should be fixed.
# Items are moved/transformed within the fixed scene.
class ScanWidget(QtWidgets.QGraphicsView):
    sigMinChanged = QtCore.Signal(object)
    sigMaxChanged = QtCore.Signal(object)
    sigNumChanged = QtCore.Signal(object)
    
    def __init__(self):
        self.scene = ScanScene()
        QtWidgets.QGraphicsView.__init__(self, self.scene)
        self.min_slider = ScanSlider()
        self.max_slider = ScanSlider()
        self.scene.addItem(self.min_slider) # , \
            # brush = QtGui.QBrush(QtGui.QColor(255,0,0,255)))
        self.scene.addItem(self.max_slider) # , \
            # brush = QtGui.QBrush(QtGui.QColor(0,0,255,255)))
        self.min_slider.sigPosChanged.connect(self.sigMinChanged)
        self.max_slider.sigPosChanged.connect(self.sigMaxChanged)
        
        
