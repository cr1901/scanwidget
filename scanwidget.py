import math

from PyQt5 import QtGui, QtCore, QtWidgets
from fractions import Fraction

# ScanAxis consists of a horizontal line extending indefinitely, major and
# minor ticks, and numbers over the major ticks. During a redraw, the width
# between adjacent ticks is recalculated, based on the new requested bounds.
#
# If the width is smaller than a certain threshold, the major ticks become
# minor ticks, and the minor ticks are deleted as objects.
# Because ScanAxis needs knowledge of units, it keeps a reference to the
# ScanSceneProxy.
class ScanAxis(QtWidgets.QGraphicsWidget):
    def __init__(self, proxy):
        QtWidgets.QGraphicsWidget.__init__(self)
        self.proxy = proxy

    def paint(self, painter, op, widget):
        sceneRect = self.scene().sceneRect()
        dispMin = sceneRect.left()
        dispMax = sceneRect.right()
        # dispRange = dispMax - dispMin
        painter.drawLine(dispMin, -4, dispMax, -4) #Qt Bug? If > -4, line is
        # erased during drag. Scene doesn't tell axis to repaint itself?
        realMin = self.proxy.sceneToReal(dispMin)
        realMax = self.proxy.sceneToReal(dispMax)
        realRange = realMax - realMin

        majorTickInc = self.floorPow10(realRange/2)
        numMajorTicks = math.ceil(realRange/majorTickInc)
        firstMajorTick = self.nearestMultipleRoundUp(realMin, majorTickInc)
        lastMajorTick = self.nearestMultipleRoundDown(realMax, majorTickInc)


        print(firstMajorTick, lastMajorTick, majorTickInc)
        # Does not work due to floating point increment.
        # The "+ majorTickInc" is so that the range is inclusive.
        # for x in range(firstMajorTick, lastMajorTick + majorTickInc, majorTickInc):
        #     painter.drawLine(self.proxy.realToScene(x), 5, self.proxy.realToScene(x), -5)
        #     painter.drawText(self.proxy.realToScene(x), -10, str(x))
        
        for x in range(numMajorTicks):
            nextTick = firstMajorTick + x*majorTickInc
            print(nextTick)
            tickLabel = str(nextTick) # May need to be reformatted.
            # tickLabel = "{:.1e}".format(nextTick)
            painter.drawLine(self.proxy.realToScene(nextTick), 5, \
                self.proxy.realToScene(nextTick), -5)
            painter.drawText(self.proxy.realToScene(nextTick), -10, tickLabel)

        # # Minor ticks
        # for i in range(dispMin, dispMax, 
        
    def floorPow10(self, val):
        if val > 0:
            return 10**math.floor(math.log10(val))
        elif val < 0:
            return -10**math.floor(math.log10(abs(val)))
        else:
            return 0

    # Only use this function in 
    def nearestMultipleRoundUp(self, val, multiple):
        return math.ceil(val/multiple)*multiple
    
    def nearestMultipleRoundDown(self, val, multiple):
        return math.floor(val/multiple)*multiple 


class DataPoint(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, pxSize = 2, color = QtGui.QColor(128,128,128,128)):
        QtWidgets.QGraphicsEllipseItem.__init__(self, 0, 0, pxSize, pxSize)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setBrush(color)
        self.setPen(color)


# ScanScene holds all the objects, and controls how events are received to
# the ScanSliders (in particular, constraining movement to the x-axis).
# TODO: SceneRect only ever has to be as large in the Y-direction as the sliders.
class ScanScene(QtWidgets.QGraphicsScene):
    (Axis, MinSlider, MaxSlider, DataPoints) = range(4)
    def __init__(self):
        QtWidgets.QGraphicsScene.__init__(self)

    def mouseMoveEvent(self, ev):
        print("Pos: ", ev.scenePos())
        QtWidgets.QGraphicsScene.mouseMoveEvent(self, ev)

    def registerItems(self, axis, minSlider, maxSlider):
        pass

    # def mouseMoveEvent(self, ev):
    #     
    # def mouseClickEvent(self, ev):
    #     pass
    # 
    # def mouseDragEvent(self, ev):
    #     pass
    # 
    # def keyPressEvent(self, ev):


# Needs to be subclassed from QGraphicsItem* b/c Qt will not send mouse events
# to GraphicsItems that do not reimplement mousePressEvent (How does Qt know?).
# Qt decides this while iterating to find which GraphicsItem should get control
# of the mouse. mousePressEvent is accepted by default.
# TODO: The slider that was most recently clicked should have z-priority.
# Qt's mouseGrab logic should implement this correctly.
# ScanSlider assumes that it's parent is the scene.
# ScanSlider does not know about other ScanSlider instances; ScanSlider knows
# about it's position in the scene/how close it is to the edges.
# ScanScene must handle object collisions.
# * Subclassed from QGraphicsObject to get signal functionality.
class ScanSlider(QtWidgets.QGraphicsObject):
    sigPosChanged = QtCore.pyqtSignal(float)
    sigBoundsUpdate = QtCore.pyqtSignal()
    
    def __init__(self, pxSize = 20, color = QtGui.QColor(128,128,128,128), bounds = 1/6):
        QtWidgets.QGraphicsItem.__init__(self)
        self.xChanged.connect(self.emitSigPosChanged)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.pxSize = pxSize
        self.color = color
        self.bounds = bounds # How close to the edge of the viewed scene
        # before we start sending boundsUpdate signal to update the "real"
        # values?

        # Make slider an equilateral triangle w/ sides pxSize pixels wide.
        altitude = math.ceil((pxSize/2)*math.sqrt(3))    
        points = [QtCore.QPoint(-(self.pxSize/2), altitude), \
            QtCore.QPoint(0, 0), QtCore.QPoint((self.pxSize/2), altitude)]
        self.shape = QtGui.QPolygon(points)

    def boundingRect(self):
        penWidth = 1 # Not user-settable.
        # If bounding box does not cover whole polygon, trails will be left
        # when the object is moved.
        return QtCore.QRectF(-self.pxSize/2 - penWidth/2, 0 - penWidth/2, \
            self.pxSize + penWidth, self.pxSize + penWidth)

    def paint(self, painter, op, widget):
        painter.setBrush(self.color)
        painter.setPen(self.color)
        painter.drawConvexPolygon(self.shape)

    def emitSigPosChanged(self):
        self.sigPosChanged.emit(self.scenePos().x())

    # Constrain movement to X axis and ensure that the sliders (bounding box?)
    # do not leave the scene.
    # TODO: Resize event for the scene should maintain current slider
    # positions or rescale the X-axis so the distance between
    # sliders and the edge of the scene remains proportional?
    def itemChange(self, change, val):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            newPos = val
            newPos.setY(0) # Constrain movement to X-axis of parent.

            rect = self.scene().sceneRect() #sceneRect will always match displayed.
            boundsRect = QtCore.QRectF(rect) # Create a copy.
            boundsLeft = self.bounds * rect.width()
            boundsRect.translate(boundsLeft, 0)
            boundsWidth = ((1 - 2 * self.bounds) * rect.width())
            assert(boundsWidth > 0) # Something really went wrong if this fails.
            boundsRect.setWidth(boundsWidth)
            print("sceneRect: ", rect)
            print("boundsRect: ", boundsRect)
            print("newPos: ", newPos)
            
            if not boundsRect.contains(newPos):
                self.sigBoundsUpdate.emit()
                newPos.setX(self.pos().x()) # Keep sliders in scene at least
                # self.bounds fraction from edge. And send a boundsUpdate.
                

            return newPos
        return QtWidgets.QGraphicsItem.itemChange(self, change, val)
    

# TODO: On a resize, should the spinbox's default increment change?
class ScanView(QtWidgets.QGraphicsView): 
    def __init__(self, zoomInc = 1.2):
        self.zoomInc = zoomInc
        # self.scene = ScanScene()
        QtWidgets.QGraphicsView.__init__(self)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter )

    def zoomOut(self):
        pass
        # self.scale(1/self.zoomInc, 1)
        # print(self.transform().m11())

    def zoomIn(self):
        pass
        # self.scale(self.zoomInc, 1)
        # print(self.transform().m11())

    def wheelEvent(self, ev):
        # if ev.delta() > 0: # TODO: Qt-4 specific.
        # TODO: If sliders are off screen after a zoom-in, what should we do?
        # TODO: If shift modifier is pressed and scroll-wheel is grazed, should
        # we honor zoom requests?
        if ev.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    # Items in scene grab mouse in this function. If shift is pressed, skip
    # deciding which slider to grab and the view itself will get mouse Events.
    # This enables adding/deleting points.
    def mousePressEvent(self, ev):
        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            pass
        else:
            QtWidgets.QGraphicsView.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):
        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            pass
        else:
            QtWidgets.QGraphicsView.mouseMoveEvent(self, ev)

    # Force the scene's boundingRect to match the view.
    def resizeEvent(self, ev):
        QtWidgets.QGraphicsView.resizeEvent(self, ev)
        self.centerOn(0, 0)
        viewportRect = QtCore.QRect(0, 0, self.viewport().width(), \
            self.viewport().height())
        sceneRectFromViewport = self.mapToScene(viewportRect).boundingRect()

        # View and Scene SceneRects are coupled until one or the other is
        # manually set. We want them coupled, but without the default rules
        # that Scene uses to set its SceneRect size.
        self.setSceneRect(sceneRectFromViewport)
        self.scene().setSceneRect(sceneRectFromViewport)
        
        # A resize will automatically fitToView to avoid having sliders go
        # out of bounds.
        
        # self.update()


# ScanSceneProxy communicates information between the what numbers are displayed
# to the user and how they map to the sliders/data stored in the scene.
# Synchronization is maintained by limiting the access to members to functions
# either called by signals, or recalculated on request.
class ScanSceneProxy(QtCore.QObject):
    sigMaxMoved = QtCore.pyqtSignal(float)
    sigMinMoved = QtCore.pyqtSignal(float)
    sigMinValChanged = QtCore.pyqtSignal(float)
    sigMaxValChanged = QtCore.pyqtSignal(float)

    def __init__(self, scene):
        QtCore.QObject.__init__(self)
        self.scene = scene
        self.units = Fraction.from_float(1.0e-15)
        # self.units = Fraction(1, 1) # Amount slider moved from user's POV per 
        # increment by one unit in the scene.
        self.bias = 0 # Number of units from scene's origin in +/- x-direction

        # Real value of sliders.
        self.min = 0
        self.max = 0
        self.numPoints = 10

    def realToScene(self, val):
        return float(Fraction(1, self.units) * Fraction.from_float(val-self.bias))

    def sceneToReal(self, val):
        return float(Fraction.from_float(val) * self.units) + self.bias

    def moveMax(self, val):
        pass
    
    # def sigMaxMoved
    # def recalculateBias(self, newMin, newMax):
    #     
    # Monitor all events sent to QGraphicsScene and update internal state
    # accordingly.
    # def eventFilter(self, obj, ev):

# The ScanWidget proper.
class ScanWidget(QtWidgets.QWidget):
    sigMinChanged = QtCore.pyqtSignal(float)
    sigMaxChanged = QtCore.pyqtSignal(float)
    sigNumChanged = QtCore.pyqtSignal(int)
    
    def __init__(self, zoomInc = 1.2):
        QtWidgets.QWidget.__init__(self)

        scene = ScanScene()
        self.view = ScanView(zoomInc)
        self.view.setScene(scene)
        self.proxy = ScanSceneProxy(scene)
        self.zoomFitButton = QtWidgets.QPushButton("Zoom to Fit")
        self.fitViewButton = QtWidgets.QPushButton("Fit to View")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.view, 0, 0, 1, -1)
        layout.addWidget(self.zoomFitButton, 1, 0)
        layout.addWidget(self.fitViewButton, 1, 1)
        self.setLayout(layout)

        axis = ScanAxis(self.proxy)
        minSlider = ScanSlider(color = QtGui.QColor(0,0,255,128))
        maxSlider = ScanSlider(color = QtGui.QColor(255,0,0,128))
        scene.addItem(axis)
        scene.addItem(minSlider)
        scene.addItem(maxSlider)

        # connect(self.
        minSlider.sigPosChanged.connect(self.proxy.sigMinMoved)
        maxSlider.sigPosChanged.connect(self.proxy.sigMaxMoved)

        self.zoomFitButton.clicked.connect(self.zoomToFit)
        self.fitViewButton.clicked.connect(self.fitToView)


# Attach these to the sliders and pushbutton signals respectively.
    def setMax(self, val):
        pass
        # emitting sigPosChanged might be moved to setPos. This will prevent
        # infinite recursion in that case.
        # if val != self.max: # WARNING: COMPARING FLOATS!
        #    pass
            # self.maxSlider.setPos(QtCore.QPointF(val, 0))
        # self.update() # Might be needed, but paint seems to occur correctly.

    def setMin(self, val):
        pass
        # if val != self.min: # WARNING: COMPARING FLOATS!
        #    pass
            # self.minSlider.setPos(QtCore.QPointF(val, 0))

    def setNumPoints(self, val):
        pass

    def zoomToFit(self):
        pass
    
    def fitToView(self):
        pass
