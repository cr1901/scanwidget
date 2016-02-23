# Robert Jordens <rj@m-labs.hk>, 2016

import numpy as np


class Ticker:
    # TODO: if this turns out to be computationally limiting, then refactor
    # such that all the log()s and intermediate values are reused. But
    # probably the string formatting itself is the limiting factor here.
    def __init__(self, min_ticks=3, precision=3, steps=(5, 2, 1, .5)):
        """
        min_ticks: minimum number of ticks to generate
            The maximum number of ticks is
            max(consecutive ratios in steps)*min_ticks
            thus 5/2*min_ticks for default steps.
        precision: maximum number of significant digits in labels
            Also extract common offset and magnitude from ticks
            if dynamic range exceeds precision number of digits
            (small range on top of large offset).
        steps: tick increments at a given magnitude
            The .5 catches rounding errors where the calculation
            of step_magnitude falls into the wrong exponent bin.
        """
        self.min_ticks = min_ticks
        self.precision = precision
        self.steps = steps

    def step(self, i):
        """
        Return recommended step value for interval size `i`.
        """
        assert i > 0
        step = i/self.min_ticks  # rational step size for min_ticks
        step_magnitude = 10**np.floor(np.log10(step))
        # underlying magnitude for steps
        for m in self.steps:
            good_step = m*step_magnitude
            if good_step <= step:
                return good_step

    def ticks(self, a, b):
        """
        Return recommended tick values for interval `[a, b[`.
        """
        step = self.step(b - a)
        a0 = np.ceil(a/step)*step
        ticks = np.arange(a0, b, step)
        return ticks

    def offset(self, a, b):
        """
        Find offset if dynamic range of the interval is large
        (small range on large offset).
        If offset is finite, show `offset + value`.
        """
        if a == 0.:
            return 0.
        la = np.floor(np.log10(abs(a)))
        lr = np.floor(np.log10(b - a))
        if la - lr < self.precision:
            return 0.
        magnitude = 10**(la - self.precision)
        offset = np.floor(a/magnitude)*magnitude
        return offset

    def magnitude(self, a, b):
        """
        Determine the scaling magnitude.

        Return scaling factor that differs from unity if the numbers
        are to be represented as `magnitude * value`.
        This depends on proper offsetting by `offset()`.
        """
        v = max(abs(a), abs(b))
        magnitude = np.floor(np.log10(v))
        if -self.precision < magnitude < self.precision:
            return 1.
        return 10**magnitude

    def fix_minus(self, s):
        return s.replace("-", "−")  # unicode minus

    def format(self, step):
        """
        Determine format string to represent step sufficiently accurate.
        """
        dynamic = -int(np.floor(np.log10(step)))
        dynamic = min(max(0, dynamic), self.precision)
        return "{{:1.{:d}f}}".format(dynamic)

    def compact_exponential(self, v):
        """
        Format `v` in in compact exponential, stripping redundant elements
        (pluses, leading and trailing zeros and decimal point, trailing `e`).
        """
        # this is after the matplotlib ScalarFormatter
        # without any i18n
        significand, exponent = "{:1.10e}".format(v).split("e")
        significand = significand.rstrip("0").rstrip(".")
        exponent_sign = exponent[0].replace("+", "")
        exponent = exponent[1:].lstrip("0")
        s = "{:s}e{:s}{:s}".format(significand, exponent_sign,
                                   exponent).rstrip("e")
        return self.fix_minus(s)

    def prefix(self, offset, magnitude):
        """
        Stringify `offset` and `magnitude`.
        """
        prefix = ""
        if offset != 0.:
            prefix += self.compact_exponential(offset) + " + "
        if magnitude != 1.:
            prefix += self.compact_exponential(magnitude) + " × "
        return prefix

    def __call__(self, a, b):
        """
        Determine step size, ticks, offset and magnitude given the interval
        `[a, b[`.

        Return array with tick value, prefix string to be show to the left or
        above the tick labels, and tick labels.
        """
        ticks = self.ticks(a, b)
        offset = self.offset(ticks[0], ticks[1])
        t = ticks - offset
        magnitude = self.magnitude(t[0], t[-1])
        t /= magnitude
        prefix = self.prefix(offset, magnitude)
        format = self.format(t[1] - t[0])
        labels = [self.fix_minus(format.format(t)) for t in t]
        return ticks, prefix, labels
