# Robert Jordens <jordens@gmail.com>, 2016

import numpy as np
import unittest


class Ticker:
    def __init__(self, n=2, dynamic=3, steps=(5, 2, 1, .5), base=10):
        # .5 for rounding errors
        self.n = n
        self.dynamic = dynamic
        self.steps = steps
        self.base = base
        self.logbase = np.log(base)

    def step(self, i, max):
        """return recommended step value for interval size i"""
        assert i > 0
        step = i/self.n
        step_mag = self.base**np.floor(np.log(step)/self.logbase)
        for m in self.steps:
            good_step = m*step_mag
            if good_step <= step:
                return good_step

    def ticks(self, a, b, max):
        """return recommended tick values for interval [a, b["""
        step = self.step(b - a, max)
        a0 = np.ceil(a/step)*step
        ticks = np.arange(a0, b, step)
        return ticks

    def offset(self, ticks):
        """find offset and magnitude if dynamic range of ticks is too large
        (small range on large offset).
        show 'offset + magnitude*' at the left and then
        use (ticks - offset)/magnitude as labels"""
        a = ticks[0]
        s = ticks[1] - ticks[0]
        if a == 0:
            return 0., 1.
        d = np.log(abs(a)/s)/self.logbase
        if d < self.dynamic:
            return 0., 1.
        e = np.floor(np.log(abs(a))/self.logbase)
        m = self.base**(e - self.dynamic)
        return np.floor(a/m)*m, m


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
            self.assertGreaterEqual((b - a)/i, t.n)
            j = t.ticks(a, b)
            self.assertGreaterEqual(j[0] + i*eps, a)
            self.assertLessEqual(j[-1] - i*eps, b)
            self.assertLess(j[0] - i*(1 + eps), a)
            self.assertGreater(j[-1] + i*(1 + eps), b)
            self.assertGreaterEqual(len(j), t.n)
            self.assertLessEqual(len(j), np.ceil(t.n*5/2))  # max step ratio
            o, m = t.offset(j)
            q = (j - o)/m
            self.assertLess(abs(q[0]/(q[1] - q[0])), 10**(t.dynamic + 1))
            if o:
                self.assertGreater(abs(j[0]/(j[1] - j[0])), 10**t.dynamic)
                self.assertGreater(q[0] + i*eps/m, 0)


if __name__ == "__main__":
    unittest.main()