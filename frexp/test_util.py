"""Unit tests for util.py."""


import unittest

from frexp.util import *


class UtilCase(unittest.TestCase):
    
    def test_stopwatch(self):
        n = 10
        def dummytimer():
            return n
        
        t = StopWatch(dummytimer)
        # Init.
        self.assertEqual(t.elapsed, 0)
        
        # Basic start/stop/elapsed usage.
        t.start()
        n = 13
        v = t.elapsed
        t.stop()
        self.assertEqual(v, 3)
        
        # Context manager usage.
        with t:
            n = 15
        self.assertEqual(t.elapsed, 5)
        
        # Consume while timing.
        with t:
            n = 17
            v = t.consume()
        self.assertEqual(v, 7)
        self.assertEqual(t.elapsed, 0)
        
        # Consume outside of timing.
        with t:
            n = 18
        v = t.consume()
        self.assertEqual(v, 1)
        self.assertEqual(t.elapsed, 0)
        
        # No double start/stop.
        t = StopWatch(dummytimer)
        with self.assertRaises(AssertionError):
            t.start()
            t.start()
        t = StopWatch(dummytimer)
        with self.assertRaises(AssertionError):
            t.stop()
            t.stop()


if __name__ == '__main__':
    unittest.main()
