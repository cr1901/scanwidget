# Robert Jordens <rj@m-labs.hk>, 2016

import numpy as np
import unittest


class Ticker:
    def __init__(self, min_ticks=3, precision=3,
                 steps=(5, 2, 1, .5), base=10):
        # the .5 in steps catches rounding errors where the calculation
        # of step_magnitude falls into the wrong exponent bin
        self.min_ticks = min_ticks  # minimum number of ticks
        # the maximum number of ticks is
        # max(consecutive ratios in steps)*min_ticks
        # thus 5/2*min_ticks
        self.precision = precision
        # maximum number of significant digits in labels
        # also extract common offset from ticks if dynamic
        # range (small range on top of large offset)
        # exceeds that many digits
        self.steps = steps  # tick increments at a given magnitude
        self.base = base  # tick number system
        self.logbase = np.log(base)

    def step(self, i):
        """return recommended step value for interval size i"""
        assert i > 0
        step = i/self.min_ticks  # rational step size for min_ticks
        step_magnitude = self.base**np.floor(np.log(step)/self.logbase)
        # underlying magnitude for steps
        for m in self.steps:
            good_step = m*step_magnitude
            if good_step <= step:
                return good_step

    def ticks(self, a, b):
        """return recommended tick values for interval [a, b["""
        step = self.step(b - a)
        a0 = np.ceil(a/step)*step
        ticks = np.arange(a0, b, step)
        return ticks

    def offset(self, a, b):
        """find offset and magnitude if dynamic range of ticks is too large
        (small range on large offset).
        show 'offset + magnitude*' at the left and then
        use (ticks - offset)/magnitude as labels"""
        assert a < b
        if a == 0.:
            return 0.
        la = np.floor(np.log(abs(a))/self.logbase)
        lr = np.floor(np.log(b - a)/self.logbase)
        if la - lr < self.precision:
            return 0.
        magnitude = self.base**(la - self.precision)
        offset = np.floor(a/magnitude)*magnitude
        return offset

    def magnitude(self, a, b):
        v = max(abs(a), abs(b))
        magnitude = np.floor(np.log(v)/self.logbase)
        if -self.precision < magnitude < self.precision:
            return 1.
        return self.base**magnitude

    def fix_minus(self, s):
        return s.replace("-", "−")  # unicode minus

    def format(self, step):
        dynamic = -int(np.floor(np.log(step)/self.logbase))
        dynamic = min(max(0, dynamic), self.precision)
        return "{{:1.{:d}f}}".format(dynamic)

    def compact_exponential(self, v):
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
        prefix = ""
        if offset != 0.:
            prefix += self.compact_exponential(offset) + " + "
        if magnitude != 1.:
            prefix += self.compact_exponential(magnitude) + " × "
        return prefix

    def __call__(self, a, b):
        ticks = self.ticks(a, b)
        offset = self.offset(ticks[0], ticks[1])
        t0 = ticks - offset
        magnitude = self.magnitude(t0[0], t0[-1])
        prefix = self.prefix(offset, magnitude)
        t1 = t0/magnitude
        format = self.format(t1[1] - t1[0])
        labels = [self.fix_minus(format.format(t)) for t in t1]
        return ticks, prefix, labels


class TickTest(unittest.TestCase):
    def test_some(self):
        for a, b, n in [
                (0, 1, 2),
                (1, 2, 2),
                (0, 1, 3),
                (-1, 1, 2),
                (1e-9, 1.1e-9, 2),
                (.3, .6, 2),
                (.3, .6, 3),
                (.3, .6, 4),
        ]:
            self._one(a, b, n)

    def _a(self):
        for a in [0, np.pi, 1, 2, 1e-6, 1e6, 1e-9, 1e9]:
            for da in [1.7e-6, 1.3e6]:
                for ra in [1.5e-6, .1]:
                    for a in -a, a:
                        for a in a, a + da, a - da:
                            for a in a, a*(1 + ra), a*(1 - ra):
                                yield a

    def _b(self, a):
        for b in (np.pi, 1, 1.1e-6, 1.9e6):
            for b in (0, b, a*b):
                yield b

    def test_many(self):
        for a in self._a():
            for b in self._b(a):
                for n in (2, 3, 4, 10):
                    if a >= b:
                        continue
                    if np.all(np.isfinite((a, b))):
                        self._one(a, b, n)

    def _one(self, a, b, n=2, d=3):
        eps = 1e-8
        with self.subTest(a=a, b=b, n=n, d=d):
            t = Ticker(n, d)
            i = t.step(b - a)
            self.assertGreaterEqual((b - a)/i, t.min_ticks)
            j = t.ticks(a, b)
            self.assertGreaterEqual(j[0] + i*eps, a)
            self.assertLessEqual(j[-1] - i*eps, b)
            self.assertLess(j[0] - i*(1 + eps), a)
            self.assertGreater(j[-1] + i*(1 + eps), b)
            self.assertGreaterEqual(len(j), t.min_ticks)
            self.assertLessEqual(len(j), np.ceil(t.min_ticks*5/2))
            # max step ratio
            o = t.offset(j[0], j[-1])
            q = j - o
            m = t.magnitude(q[0], q[-1])
            q = q/m
            self.assertLess(abs(q[0]/(q[1] - q[0])),
                            10**(t.precision + 1))
            if o:
                self.assertGreater(abs(j[0]/(j[1] - j[0])),
                                   10**t.precision)
                self.assertGreater(q[0] + i*eps/m, 0)
            ticks, prefix, labels = t(a, b)
            self.assertEqual(sorted(set(labels)), sorted(labels))
            v = [eval((prefix + l).replace("−", "-"))  # unicode minus
                 for l in labels]
            np.testing.assert_allclose(ticks, v,
                                       rtol=t.base**-t.precision,
                                       atol=1e-13*i)


if __name__ == "__main__":
    unittest.main()
