import unittest
import numpy as np

from ticker import Ticker


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
                (1000.0001, 1000.0002, 3),
                (1234567.89123, 1234567.89124, 3),
                (1234567.8, 1234567.9, 30),
                (3.1349, 3.1415, 9),
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
        yield 0
        for b in (np.pi, 1, 1.1e-6, 1.9e6):
            for b in (b, a*b):
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
            # ticks, prefix, labels = t(a, b)
            # print(a, b, ticks, prefix, labels)

            i = t.step(b - a)
            self.assertGreaterEqual((b - a)/i, t.min_ticks)
            j = t.ticks(a, b)
            self.assertGreaterEqual(j[0] + i*eps, a)
            self.assertLess(j[0] - i*(1 + eps), a)
            self.assertLessEqual(j[-1] - i*eps, b)
            self.assertGreater(j[-1] + i*(1 + eps), b)
            self.assertGreaterEqual(len(j), t.min_ticks)
            self.assertLessEqual(len(j), np.ceil(t.min_ticks*5/2))
            o = t.offset(j[0], j[1] - j[0])
            q = j - o
            m = t.magnitude(q[0], q[-1], q[1] - q[0])
            q = q/m
            self.assertLess(abs(q[0]/(q[1] - q[0])), 10**(t.precision + 1))
            if o:
                # not the only reason:
                # self.assertGreater(abs(j[0]/(j[1] - j[0])), 10**t.precision)
                self.assertGreater(q[0] + i*eps/m, 0)

            ticks, prefix, labels = t(a, b)
            self.assertEqual(sorted(set(labels)), sorted(labels))
            v = [eval((prefix + l).replace("−", "-").replace("×", "*"))
                 for l in labels]
            np.testing.assert_allclose(ticks, v, atol=2e-14*i)


if __name__ == "__main__":
    unittest.main()
