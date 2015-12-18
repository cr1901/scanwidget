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


class DataPoint(QtWidgets.QGraphicsItem):
    def __init__(self):
        pass
# class ScanModel(QO


# ScanScene holds all the objects, and controls how events are received to
# the ScanSliders (in particular, constraining movement to the x-axis).
class ScanScene(QtWidgets.QGraphicsScene):
    def __init__(self):
        QtWidgets.QGraphicsScene.__init__(self)

    def mouseMoveEvent(self, ev):
        QtWidgets.QGraphicsScene.mouseMoveEvent(self, ev)
        
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

# Houses the ScanAxis and Sliders in one row, buttons which auto-scale the view
# in another. Also 

# Needs to be subclassed from QGraphicsItem* b/c Qt will not send mouse events
# to GraphicsItems that do not reimplement mousePressEvent (How does Qt know?).
# Qt decides this while iterating to find which GraphicsItem should get control
# of the mouse. mousePressEvent is accepted by default.
# TODO: The slider that was most recently clicked should have z-priority.
# Qt's mouseGrab logic should implement this correctly.
# * Subclassed from QGraphicsObject to get signal functionality.
class ScanSlider(QtWidgets.QGraphicsObject):
    sigPosChanged = QtCore.pyqtSignal(float)
    
    def __init__(self, pxSize = 20, color = QtGui.QBrush(QtGui.QColor(128,128,128,128))):
        QtWidgets.QGraphicsItem.__init__(self)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.pxSize = pxSize
        self.color = color
        
        # Make slider an equilateral triangle w/ sides pxSize pixels wide.
        altitude = math.ceil((pxSize/2)*math.sqrt(3))
        
        points = [QtCore.QPoint(-(self.pxSize/2), altitude), \
            QtCore.QPoint(0, 0), QtCore.QPoint((self.pxSize/2), altitude)]
        self.shape = QtGui.QPolygon(points)

    def boundingRect(self):
        #TODO: Set based on whatever user passed in to create QPen.
        penWidth = 1
        # If bounding box does not cover whole polygon, trails will be left
        # when the object is moved.
        return QtCore.QRectF(-self.pxSize/2 - penWidth/2, 0 - penWidth/2, \
            self.pxSize + penWidth, self.pxSize + penWidth)

    def paint(self, painter, op, widget):
        painter.setBrush(self.color)
        painter.setPen(self.color)
        painter.drawConvexPolygon(self.shape)

    def mousePressEvent(self, ev):
        QtWidgets.QGraphicsItem.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):
        QtWidgets.QGraphicsItem.mouseMoveEvent(self, ev)
        self.sigPosChanged.emit(self.scenePos().x())
        

# TODO: Is it scene's responsibility or item's responsibility to ensure item stays
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
    sigMinChanged = QtCore.pyqtSignal(float)
    sigMaxChanged = QtCore.pyqtSignal(float)
    sigNumChanged = QtCore.pyqtSignal(int)
    
    def __init__(self):
        self.scene = ScanScene()
        QtWidgets.QGraphicsView.__init__(self, self.scene)
        # self.setSceneRect(self.frameGeometry()) # Ensure no scrollbars.
        
        self.minSlider = ScanSlider(color = QtGui.QColor(0,0,255,128))
        self.maxSlider = ScanSlider(color = QtGui.QColor(255,0,0,128))
        self.scene.addItem(self.minSlider)
        self.scene.addItem(self.maxSlider)
        self.minSlider.sigPosChanged.connect(self.sigMinChanged)
        self.maxSlider.sigPosChanged.connect(self.sigMaxChanged)
    
    def zoomOut(self):
        self.scale(1/1.2, 1/1.2)

    def zoomIn(self):
        self.scale(1.2, 1.2)

    def wheelEvent(self, ev):
        # if ev.delta() > 0: # TODO: Qt-4 specific.
        # TODO: If sliders are off screen after a zoom-in, what should we do?
        if ev.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()
        
    # def resizeEvent(self):
    #     pass
    
