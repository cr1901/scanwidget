import math

from PyQt5 import QtGui, QtCore, QtWidgets
from fractions import Fraction

# ScanAxis consists of a horizontal line extending indefinitely, major and
# minor ticks, and numbers over the major ticks. During a redraw, the width
# between adjacent ticks is recalculated, based on the new requested bounds.
#
# If the width is smaller than a certain threshold, the major ticks become
# minor ticks, and the minor ticks are deleted as objects.
# Because ScanAxis needs knowledge of units and viewport, it keeps a reference to the
# ScanSceneProxy and View.
class ScanAxis(QtWidgets.QGraphicsWidget):
    def __init__(self, proxy, view):
        QtWidgets.QGraphicsWidget.__init__(self)
        self.proxy = proxy
        self.boundingRectCopy = QtCore.QRectF()
        self.view = view

    def boundingRect(self):
        return self.boundingRectCopy

    def paint(self, painter, op, widget):
        sceneRect = self.scene().sceneRect()
        # assert self.view.sceneRectFromViewport() == sceneRect, "viewport {0}, scene {1}".format(self.view.sceneRectFromViewport(), sceneRect)
        dispMin = sceneRect.left()
        dispMax = sceneRect.right()
        painter.drawLine(dispMin, -1, dispMax, -1)
        realMin = self.proxy.sceneToReal(dispMin)
        realMax = self.proxy.sceneToReal(dispMax)
        realRange = realMax - realMin

        majorTickInc = self.floorPow10(realRange/2)
        numMajorTicks = math.ceil(realRange/majorTickInc)
        firstMajorTick = self.nearestMultipleRoundUp(realMin, majorTickInc)
        lastMajorTick = self.nearestMultipleRoundDown(realMax, majorTickInc)

        # Does not work due to floating point increment.
        # The "+ majorTickInc" is so that the range is inclusive.
        # for x in range(firstMajorTick, lastMajorTick + majorTickInc, majorTickInc):
        #     painter.drawLine(self.proxy.realToScene(x), 5, self.proxy.realToScene(x), -5)
        #     painter.drawText(self.proxy.realToScene(x), -10, str(x))
        
        for x in range(numMajorTicks):
            nextTick = firstMajorTick + x*majorTickInc
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

    # We need to register items later b/c axis and datapoints reference the
    # proxy for information, but proxy needs the scene to have been created.
    def registerItems(self, axis, minSlider, maxSlider):
        self.axis = axis
        self.minSlider = minSlider
        self.maxSlider = maxSlider
        self.addItem(axis)
        self.addItem(minSlider)
        self.addItem(maxSlider)

    # Get a rectangle in scene coords that is at the same position as sceneRect
    # but is smaller on each side by bounds proportion.
    def getCenteredRect(self, bounds):
        rect = self.sceneRect() #sceneRect will always match displayed.
        boundsRect = QtCore.QRectF(rect) # Create a copy.
        boundsLeft = bounds * rect.width()
        boundsRect.translate(boundsLeft, 0)
        boundsWidth = ((1 - 2 * bounds) * rect.width())
        assert(boundsWidth > 0) # Something really went wrong if this fails.
        boundsRect.setWidth(boundsWidth)
        return boundsRect
        

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
    sigBoundsUpdate = QtCore.pyqtSignal()
    
    def __init__(self, pxSize = 20, color = QtGui.QColor(128,128,128,128), bounds = 1/100):
        QtWidgets.QGraphicsItem.__init__(self)
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

    # Constrain movement to X axis and ensure that the sliders (bounding box?)
    # do not leave the scene.
    # TODO: Resize event for the scene should maintain current slider
    # positions or rescale the X-axis so the distance between
    # sliders and the edge of the scene remains proportional?
    def itemChange(self, change, val):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            newPos = val
            newPos.setY(0) # Constrain movement to X-axis of parent.
            boundsRect = self.scene().getCenteredRect(self.bounds)

            # print("sceneRect: ", self.scene().sceneRect())
            # print("boundsRect: ", boundsRect)
            # print("newPos: ", newPos)
            
            if not boundsRect.contains(newPos):
                newPos.setX(self.pos().x()) # Keep sliders in scene at least
                # self.bounds fraction from edge. And send a boundsUpdate.
                # print("sigBoundsUpdate")
                self.sigBoundsUpdate.emit()
                self.xChanged.emit() # If incrementing a spinbox caused the
                # sliders to go out of bounds, we need to notify the spinboxes
                # that the increment was not honored and restore the original value.
                

            return newPos
        return QtWidgets.QGraphicsItem.itemChange(self, change, val)
    

# TODO: On a resize, should the spinbox's default increment change?
class ScanView(QtWidgets.QGraphicsView): 
    sigZoom = QtCore.pyqtSignal(int)
    def __init__(self):
        QtWidgets.QGraphicsView.__init__(self)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter )

    def wheelEvent(self, ev):
        # if ev.delta() > 0: # TODO: Qt-4 specific.
        # TODO: If sliders are off screen after a zoom-in, what should we do?
        # TODO: If shift modifier is pressed and scroll-wheel is grazed, should
        # we honor zoom requests?
        if ev.angleDelta().y() > 0:
            self.sigZoom.emit(1)
        else:
            self.sigZoom.emit(-1)

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

    def sceneRectFromViewport(self):
        viewportRect = QtCore.QRect(0, 0, self.viewport().width(), \
            self.viewport().height())
        return self.mapToScene(viewportRect).boundingRect()

    # Force the scene's boundingRect to match the view. Also ensure axis and
    # datapoints are updated.
    def resizeEvent(self, ev):        
        QtWidgets.QGraphicsView.resizeEvent(self, ev)
        self.centerOn(0, 0) # Resizes to make the viewed scene smaller will
        # be off-center without this.
        # TODO: What is the source of the off-by-one error? Viewed scene
        # starts drifting without this correction.
        
        sceneRectFromViewport = self.sceneRectFromViewport()
        # print("sceneRectFromViewport", sceneRectFromViewport)
        # print("view.sceneRect", self.sceneRect().left(), self.sceneRect().top())
        print("viewport rect", self.viewport().rect())

        # View and Scene SceneRects are coupled until one or the other is
        # manually set. We want them coupled, but without the default rules
        # that Scene uses to set its SceneRect size.
        self.setSceneRect(sceneRectFromViewport)
        self.scene().setSceneRect(sceneRectFromViewport)
        
        # Lovely dependency hell here. Axis must match viewport size...
        # * Axis cannot call sceneRect() to get scene size in 
        # boundingRect() b/c infinite recursion.
        # * GraphicsView resizeEvent will call GraphicsScene resize event. Axis
        # depends on new size, so boundingRect calculation must be deferred.
        # * The axis' new size must be set manually.
        # * Refactor into ScanScene-specific method?
        self.scene().axis.boundingRectCopy = self.scene().sceneRect()
        self.scene().axis.prepareGeometryChange()
        
        # A resize will automatically fitToView to avoid having sliders go
        # out of bounds.


# ScanSceneProxy communicates information between the what numbers are displayed
# to the user and how they map to the sliders/data stored in the scene.
# Synchronization is maintained by limiting the access to members to functions
# either called by signals, or recalculated on request.
# ScanScene and ScanSliders know nothing about the mapping (ScanAxis does).
# Consequently, they cannot distinguish an xChanged from having their value
# changed versus a change in the mapping.
class ScanSceneProxy(QtCore.QObject):
    sigMaxMoved = QtCore.pyqtSignal(float)
    sigMinMoved = QtCore.pyqtSignal(float)
    sigMinValChanged = QtCore.pyqtSignal(float)
    sigMaxValChanged = QtCore.pyqtSignal(float)

    def __init__(self, scene):
        QtCore.QObject.__init__(self)
        self.scene = scene
        # self.units = Fraction.from_float(1.0e-16)
        self.units = Fraction(1, 1) # Amount slider moved from user's POV per 
        # increment by one unit (pixel) in the scene.
        self.bias = 0 # Center of viewed scene maps to this point.

        # Real value of sliders.
        self.numPoints = 10

    def realToScene(self, val):
        return float(Fraction(1, self.units) * Fraction.from_float(val-self.bias))

    # Get a point from pixel units to what the sliders display.
    def sceneToReal(self, val):
        return float(Fraction.from_float(val) * self.units) + self.bias

    def moveMax(self, val):
        desiredX = self.realToScene(val)
        currentX = self.scene.maxSlider.pos().x()
        # Prevent signal recursion if the value sent equals the current
        # position of the slider in the scene.
        if desiredX != currentX:
            self.scene.maxSlider.setX(desiredX)

    def moveMin(self, val):
        desiredX = self.realToScene(val)
        currentX = self.scene.minSlider.pos().x()
        # Prevent signal recursion if the value sent equals the current
        # position of the slider in the scene.
        if desiredX != currentX:
            self.scene.minSlider.setX(desiredX)

    # TODO: Any way to get rid of assumption that scene will have a
    # max/minSlider field?
    def getMax(self):
        return self.sceneToReal(self.scene.maxSlider.pos().x())

    def getMin(self):
        return self.sceneToReal(self.scene.minSlider.pos().x())

    def maxChanged(self): 
        self.sigMaxValChanged.emit(self.getMax())

    def minChanged(self):
        self.sigMinValChanged.emit(self.getMin())

    def recalculateUnitsOnBounds(self):
        pass

    def handleZoom(self, zoomDir):
        if zoomDir > 0:
            self.recalculateUnitsOnZoom(Fraction(4, 5))
        else:
            self.recalculateUnitsOnZoom(Fraction(6, 5))

    # zoomFactor should be a fraction. Note that this is relative to the current
    # zoomFactor.
    def recalculateUnitsOnZoom(self, zoomFactor, *args):
        currMax = self.getMax()
        currMin = self.getMin()
        self.units = Fraction(self.units * zoomFactor)
        print("units: ", self.units)
        if args:
            self.bias = args[0]
        print("bias: ", self.bias)
        self.moveMax(currMax)
        self.moveMin(currMin)
        self.scene.axis.update()

    def zoomToFit(self):
        rect = self.scene.sceneRect() # sceneRect is as big as view.
        currMax = self.getMax() # When zooming to Fit, do NOT alter curr
        currMin = self.getMin()
        currRange = (currMax - currMin)
        if currRange > 0: # Do not honor malformed ranges.
            # Determine the zoomFactor required so that currRange is 2/3 of
            # sceneRect based on units/pixel value.
            targetRect = self.scene.getCenteredRect(1/3)
            targetRectRange = self.sceneToReal(targetRect.right()) - \
                self.sceneToReal(targetRect.left())
            print("currRange", currRange)
            print("targetRectRange", targetRectRange)
            
            newBias = currMin + currRange/2 # Translate center to middle of max/min.
            # targetRectRange = k*currRange; k = targetRectRange/currRange.
            # If k > 1, we want to increase distance between sliders- zoom in.
            # However, zoomFactor by k actually zooms out by 1/k due to the
            # how units are kept, so invert the fraction.
            newZoom = Fraction.from_float(currRange) / \
                Fraction.from_float(targetRectRange)
            # Now that the new units have been registered, move the sliders
            # and update the axis. Values kept by the proxy haven't changed; only
            # the positions within the scene based on updated proxy.
            self.recalculateUnitsOnZoom(newZoom, newBias)
            
    def fitToView(self):
        targetRect = self.scene.getCenteredRect(1/3)
        print(targetRect)
        newMin = self.sceneToReal(targetRect.left())
        newMax = self.sceneToReal(targetRect.right())
        self.moveMin(newMin)
        self.moveMax(newMax)


# The ScanWidget proper.
class ScanWidget(QtWidgets.QWidget):
    sigMinChanged = QtCore.pyqtSignal(float)
    sigMaxChanged = QtCore.pyqtSignal(float)
    sigNumChanged = QtCore.pyqtSignal(int)
    
    def __init__(self, zoomInc = 1.2):
        QtWidgets.QWidget.__init__(self)

        scene = ScanScene()
        self.view = ScanView()
        self.view.setScene(scene)
        self.proxy = ScanSceneProxy(scene)
        self.zoomFitButton = QtWidgets.QPushButton("Zoom to Fit")
        self.fitViewButton = QtWidgets.QPushButton("Fit to View")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.view, 0, 0, 1, -1)
        layout.addWidget(self.zoomFitButton, 1, 0)
        layout.addWidget(self.fitViewButton, 1, 1)
        self.setLayout(layout)

        axis = ScanAxis(self.proxy, self.view)
        minSlider = ScanSlider(color = QtGui.QColor(0,0,255,128))
        maxSlider = ScanSlider(color = QtGui.QColor(255,0,0,128))
        scene.registerItems(axis, minSlider, maxSlider)
        

        # Connect signals.
        # min/maxChanged fcns will convert data from pixel coordinates to
        # real coordinates, then emit sigMin/MaxChanged.
        minSlider.xChanged.connect(self.proxy.minChanged)
        maxSlider.xChanged.connect(self.proxy.maxChanged)
        self.proxy.sigMinValChanged.connect(self.sigMinChanged)
        self.proxy.sigMaxValChanged.connect(self.sigMaxChanged)

        self.view.sigZoom.connect(self.proxy.handleZoom)

        self.zoomFitButton.clicked.connect(self.zoomToFit)
        self.fitViewButton.clicked.connect(self.fitToView)


# Attach these to the sliders and pushbutton signals respectively.
    def setMax(self, val):
        self.proxy.moveMax(val)

    def setMin(self, val):
        self.proxy.moveMin(val)

    def setNumPoints(self, val):
        pass

    def zoomToFit(self):
        self.proxy.zoomToFit()
    
    def fitToView(self):
        self.proxy.fitToView()
