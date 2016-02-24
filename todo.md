## To Fix (Bugs)
* Lying about the slider-to-pixel transform to the proxy can cause infinite signal recursion when the spinboxes are updated.
* At large zooms, the sliders start taking the wrong positions due to floating point errors?
* Check that recalculating the zoom transform in fact has a relative error of 10^-15, not absolute error. If latter, rethink transform.
* Remove asserts (or catch AssertionFailure) and just refuse to honor zooms at some point.

## To Modify (Not technically broken, but needs to be changed on request)
* Scroll wheel zoom needs to be fixed per the following discussion with sb0:
    * sb0: Just to reiterate, the behavior you want is that if you zoom the mouse if the cursor is in the center of two overlapped sliders, the sliders should separate equal distance (in pixels) relative to the center of your zoom.
    * rjo: in other words: the origin/center of the zoom is the cursor position, a.k.a the value under the cursor stays where it is when zooming.
* Change slider behavior so that sliders can cross/overlap.
* Make zoom, (1/n, (n-1)/n) placement, user-settable, exposed in ScanWidget attributes (just programmatically, no need for runtime configurability)

## To Implement
* Implement slider hiding when zoom causes sliders to disappear.
* Add number of points functionality+shift-drag.
* Convert FitToView and ZoomToFit to context menu, add Reset.
* Add tick mark visualization for number of points.
* Axis widget should capture scroll events from slider.