import math

from PyQt5 import QtGui, QtCore, QtWidgets
from fractions import Fraction


class ScanAxis(QtWidgets.QWidget):
    sigZoom = QtCore.pyqtSignal(int)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.proxy = None
        self.sizePolicy().setControlType(QtWidgets.QSizePolicy.ButtonBox)

    def paintEvent(self, ev):
        painter = QtGui.QPainter(self)
        # painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pixMin = -self.width() / 2
        pixMax = -pixMin
        painter.translate(self.width() / 2, self.height() - 5)
        painter.drawLine(pixMin, 0, pixMax, 0)
        realMin = self.proxy.pixelToReal(pixMin)
        realMax = self.proxy.pixelToReal(pixMax)
        realRange = realMax - realMin

        majorTickInc = self.floorPow10(realRange / 2)
        numMajorTicks = math.ceil(realRange / majorTickInc)
        firstMajorTick = self.nearestMultipleRoundUp(realMin, majorTickInc)
        lastMajorTick = self.nearestMultipleRoundDown(realMax, majorTickInc)

        for x in range(numMajorTicks):
            nextTick = firstMajorTick + x * majorTickInc
            # tickLabel = str(nextTick) # May need to be reformatted.
            tickLabel = "{:.1e}".format(nextTick)
            painter.drawLine(self.proxy.realToPixel(nextTick), 5,
                             self.proxy.realToPixel(nextTick), -5)
            painter.drawText(self.proxy.realToPixel(nextTick), -10, tickLabel)

    def wheelEvent(self, ev):
        # if ev.delta() > 0: # TODO: Qt-4 specific.
        # TODO: If sliders are off screen after a zoom-in, what should we do?
        # TODO: If shift modifier is pressed and scroll-wheel is grazed, should
        # we honor zoom requests?
        if ev.angleDelta().y() > 0:
            self.sigZoom.emit(1)
        else:
            self.sigZoom.emit(-1)
        self.update()

    def floorPow10(self, val):
        if val > 0:
            return 10**math.floor(math.log10(val))
        elif val < 0:
            return -10**math.floor(math.log10(abs(val)))
        else:
            return 0

    def nearestMultipleRoundUp(self, val, multiple):
        return math.ceil(val / multiple) * multiple

    def nearestMultipleRoundDown(self, val, multiple):
        return math.floor(val / multiple) * multiple


# Reimplemented from https://gist.github.com/Riateche/27e36977f7d5ea72cf4f,
# with extra functionality removed and some function/variables renamed.
class ScanSlider(QtWidgets.QSlider):
    sigMinMoved = QtCore.pyqtSignal(int)
    sigMaxMoved = QtCore.pyqtSignal(int)
    (noSlider, minSlider, maxSlider) = range(3)

    def __init__(self):
        QtWidgets.QSlider.__init__(self, QtCore.Qt.Horizontal)
        self.minPos = 0  # Pos and Val can differ in event handling.
        # perhaps prevPos and currPos is more accurate.
        self.maxPos = 99
        self.minVal = 0  # lower
        self.maxVal = 99  # upper
        self.offset = 0
        self.position = 0
        self.lastPressed = ScanSlider.noSlider
        self.selectedHandle = ScanSlider.minSlider
        self.upperPressed = QtWidgets.QStyle.SC_None
        self.lowerPressed = QtWidgets.QStyle.SC_None
        self.firstMovement = False  # State var for handling slider overlap.
        self.blockTracking = False

    # We basically superimpose two QSliders on top of each other, discarding
    # the state that remains constant between the two when drawing.
    # Everything except the handles remain constant.
    def initHandleStyleOption(self, opt, handle):
        self.initStyleOption(opt)
        if handle == ScanSlider.minSlider:
            opt.sliderPosition = self.minPos
            opt.sliderValue = self.minVal
        elif handle == ScanSlider.maxSlider:
            opt.sliderPosition = self.maxPos
            opt.sliderValue = self.maxVal
        else:
            pass  # AssertionError

    # We get the range of each slider separately.
    def pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)

        gr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderHandle, self)

        # TODO: Slider's middle (not left) should be what the range value
        # reflect?
        sliderLength = sr.width()
        sliderMin = gr.x()
        # Presumably rectangles overlap at right edge?
        sliderMax = gr.right() - sliderLength + 1

        return QtWidgets.QStyle.sliderValueFromPosition(self.minimum(),
                                                        self.maximum(), pos - sliderMin, sliderMax - sliderMin,
                                                        opt.upsideDown)

    def rangeValueToPixelPos(self, val):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)

        gr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderHandle, self)

        sliderLength = sr.width()
        sliderMin = gr.x()
        sliderMax = gr.right() - sliderLength + 1

        pixel = QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                                                         self.maximum(), val, sliderMax - sliderMin, opt.upsideDown)
        return pixel

    def handleMousePress(self, pos, control, val, handle):
        opt = QtWidgets.QStyleOptionSlider()
        self.initHandleStyleOption(opt, handle)
        oldControl = control
        control = self.style().hitTestComplexControl(
            QtWidgets.QStyle.CC_Slider, opt, pos, self)
        sr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderHandle, self)
        if control == QtWidgets.QStyle.SC_SliderHandle:
            # no pick()- slider orientation static
            self.offset = pos.x() - sr.topLeft().x()
            self.lastPressed = handle
            self.setSliderDown(True)
            self.selectedHandle = handle
            # emit

        # Needed?
        if control != oldControl:
            self.update(sr)
        return control

    def drawHandle(self, painter, handle):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        self.initHandleStyleOption(opt, handle)
        opt.subControls = QtWidgets.QStyle.SC_SliderHandle
        painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt)

    # def triggerAction(self, action, slider):
    #     if action == QtWidgets.QAbstractSlider.SliderSingleStepAdd:
    #         if

    def setLowerValue(self, val):
        self.setSpan(val, self.maxVal)

    def setUpperValue(self, val):
        self.setSpan(self.minVal, val)

    def setSpan(self, lower, upper):
        def bound(min, curr, max):
            if curr < min:
                return min
            elif curr > max:
                return max
            else:
                return curr

        low = bound(self.minimum(), lower, self.maximum())
        high = bound(self.minimum(), upper, self.maximum())

        if low != self.minVal or high != self.maxVal:
            if low != self.minVal:
                self.minVal = low
                self.minPos = low
                # emit
            if high != self.maxVal:
                self.maxVal = high
                self.maxPos = high
                # emit
            # emit spanChanged
            self.update()

    def setLowerPosition(self, val):
        if val != self.minPos:
            self.minPos = val
            if not self.hasTracking():
                self.update()
            if self.isSliderDown():
                pass
                # emit lowerPositionChanged
            if self.hasTracking() and not self.blockTracking:
                self.setLowerValue(val)

    def setUpperPosition(self, val):
        if val != self.maxPos:
            self.maxPos = val
            if not self.hasTracking():
                self.update()
            if self.isSliderDown():
                pass
                # emit upperPositionChanged
            if self.hasTracking() and not self.blockTracking:
                self.setUpperValue(val)

    def mousePressEvent(self, ev):
        if self.minimum() == self.maximum() or (ev.buttons() ^ ev.button()):
            ev.ignore()
            return

        # Prefer maxVal in the default case.
        self.upperPressed = self.handleMousePress(ev.pos(), self.upperPressed,
                                                  self.maxVal, ScanSlider.maxSlider)
        if self.upperPressed != QtWidgets.QStyle.SC_SliderHandle:
            self.lowerPressed = self.handleMousePress(ev.pos(),
                                                      self.upperPressed, self.minVal, ScanSlider.minSlider)

        # State that is needed to handle the case where two sliders are equal.
        self.firstMovement = True
        ev.accept()

    def mouseMoveEvent(self, ev):
        if self.lowerPressed != QtWidgets.QStyle.SC_SliderHandle and \
                self.upperPressed != QtWidgets.QStyle.SC_SliderHandle:
            ev.ignore()
            return

        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)

        # This code seems to be needed so that returning the slider to the
        # previous position is honored if a drag distance is exceeded.
        m = self.style().pixelMetric(QtWidgets.QStyle.PM_MaximumDragDistance, opt, self)
        newPos = self.pixelPosToRangeValue(ev.pos().x() - self.offset)

        if m >= 0:
            r = self.rect().adjusted(-m, -m, m, m)
            if not r.contains(ev.pos()):
                newPos = self.position

        if self.firstMovement:
            if self.minPos == self.maxPos:
                # MaxSlider is preferred, except in the case where min == max
                # possible value the slider can take.
                if self.minPos == self.maximum():
                    self.lowerPressed = QtWidgets.QStyle.SC_SliderHandle
                    self.upperPressed = QtWidgets.QStyle.SC_None
                self.firstMovement = False

        if self.lowerPressed == QtWidgets.QStyle.SC_SliderHandle:
            newPos = min(newPos, self.maxVal)
            self.setLowerPosition(newPos)

        if self.upperPressed == QtWidgets.QStyle.SC_SliderHandle:
            newPos = max(newPos, self.minVal)
            self.setUpperPosition(newPos)

        ev.accept()

    def mouseReleaseEvent(self, ev):
        QtWidgets.QSlider.mouseReleaseEvent(self, ev)
        self.setSliderDown(False)  # AbstractSlider needs this
        self.lowerPressed = QtWidgets.QStyle.SC_None
        self.upperPressed = QtWidgets.QStyle.SC_None

    def paintEvent(self, ev):
        # Use a QStylePainter to make redrawing as painless as possible.
        painter = QtWidgets.QStylePainter(self)

        # Groove
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt)

        # Handles
        self.drawHandle(painter, ScanSlider.minSlider)
        self.drawHandle(painter, ScanSlider.maxSlider)
        # self.initHandleStyleOption(opt, ScanSlider.maxSlider)
        # painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt)

        # opt.sliderPosition = self.maxPos
        # opt.sliderValue = self.maxVal
        # painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt)


# real (Sliders) => pixel (one pixel movement of sliders would increment by X)
# => range (minimum granularity that sliders understand).
class ScanProxy(QtCore.QObject):

    def __init__(self, slider, axis):
        QtCore.QObject.__init__(self)
        self.axis = axis
        self.slider = slider
        self.units = Fraction(1, 1)
        self.bias = 0
        self.numPoints = 10

    def realToPixel(self, val):
        return float(Fraction(1, self.units) * Fraction.from_float(val - self.bias))

    # Get a point from pixel units to what the sliders display.
    def pixelToReal(self, val):
        return float(Fraction.from_float(val) * self.units) + self.bias

    def moveMax(self, val):
        pass
    #    proxyX = self.realToPixel(val)
    #    desiredSliderX = self.slider.pixelPosToRangeValue(proxyX)
    #    currentSliderX = self.slider.maxPos
    #
    #    # Signal recursion guard.
    #    if desiredSliderX != currentSliderX:
    #        self.slider.setUpperPosition(desiredSliderX)

    def moveMin(self, val):
        pass
    #     desiredX = self.realToScene(val)
    #     currentX = self.scene.minSlider.pos().x()
    #     # Prevent signal recursion if the value sent equals the current
    #     # position of the slider in the scene.
    #     if desiredX != currentX:
    #         self.scene.minSlider.setX(desiredX)
    #
    # # TODO: Any way to get rid of assumption that scene will have a
    # # max/minSlider field?

    def getMax(self):
        pass
        # return self.sceneToReal(self.scene.maxSlider.pos().x())

    def getMin(self):
        pass
        # return self.sceneToReal(self.scene.minSlider.pos().x())

    # def maxChanged(self):
    #     self.sigMaxValChanged.emit(self.getMax())
    #
    # def minChanged(self):
    #     self.sigMinValChanged.emit(self.getMin())
    #
    # def recalculateUnitsOnBounds(self):
    #     pass
    #
    def handleZoom(self, zoomDir):
        if zoomDir > 0:
            self.recalculateUnitsOnZoom(Fraction(4, 5))
        else:
            self.recalculateUnitsOnZoom(Fraction(6, 5))

    def recalculateUnitsOnZoom(self, zoomFactor, *args):
        currMax = self.getMax()
        currMin = self.getMin()
        self.units = Fraction.from_float(float(self.units * zoomFactor))
        print("units: ", self.units)
        if args:
            self.bias = args[0]
        print("bias: ", self.bias)
        self.moveMax(currMax)
        self.moveMin(currMin)
        # self.axis.repaint() # No longer works for some reason...


class ScanWidget(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        slider = ScanSlider()
        axis = ScanAxis()
        zoomFitButton = QtWidgets.QPushButton("Zoom to Fit")
        fitViewButton = QtWidgets.QPushButton("Fit to View")
        self.proxy = ScanProxy(slider, axis)
        axis.proxy = self.proxy
        self.axis = axis

        layout = QtWidgets.QGridLayout()
        # Default size will cause axis to disappear otherwise.
        layout.setRowMinimumHeight(0, 25)
        layout.addWidget(axis, 0, 0, 1, -1)
        layout.addWidget(slider, 1, 0, 1, -1)
        layout.addWidget(zoomFitButton, 2, 0)
        layout.addWidget(fitViewButton, 2, 1)
        self.setLayout(layout)

        self.axis.sigZoom.connect(self.proxy.handleZoom)

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
