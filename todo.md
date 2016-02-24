## To Fix (Bugs)
* Lying about the slider-to-pixel transform to the proxy can cause infinite signal recursion when the spinboxes are updated.
* At large zooms, the sliders start taking the wrong positions due to floating point errors?
* Check that recalculating the zoom transform in fact has a relative error of 10^-15, not absolute error. If latter, rethink transform.
* Remove asserts (or catch AssertionFailure) and just refuse to honor zooms at some point.
* Many more slider positions than 100

## To Modify (Not technically broken, but needs to be changed on request)
* Scroll wheel zoom needs to be fixed per the following discussion with sb0:
    * sb0: Just to reiterate, the behavior you want is that if you zoom the mouse if the cursor is in the center of two overlapped sliders, the sliders should separate equal distance (in pixels) relative to the center of your zoom.
    * rjo: in other words: the origin/center of the zoom is the cursor position, a.k.a the value under the cursor stays where it is when zooming.
* Change slider behavior so that sliders can cross/overlap.
    * Rename Min/Max (and Lower/Upper?) terminology to Start/Stop
* Make zoom, (1/n, (n-1)/n) placement, user-settable, exposed in ScanWidget attributes (just programmatically, no need for runtime configurability)
* Center tick labels above ticks

## To Implement
* Implement slider hiding when zoom causes sliders to disappear.
* Add number of points functionality
    * visualize on axis
    * change on shift-wheelEvent
* Drag modes:
    * drag axis: move axis origin
    * shift-drag axis: move both sliders (and thus all scanned points, analogous to shift-wheelEvent)
* Convert FitToView and ZoomToFit to context menu, add Reset.
* Add tick mark visualization for number of points.
* Axis widget should capture scroll events from slider.

## Improvements
* Spin boxes should use scientific notation. When updated, they should show
  "{:g}".format(value). When changed, they should keep the value but validate
  and use float(input).
* When dragging a slider, it should snap (-> spinboxes) to "nice" values. The
  Something like rounding to Ticker().step() should be sufficient.
