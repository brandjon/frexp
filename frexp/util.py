"""Miscellaneous small utilities."""


__all__ = [
    'StopWatch',
    
    'on_battery_power',
    
    'get_mem_usage',
]


import time
import sys
import os


class StopWatch:
    
    """Resumable timer. Can be manipulated by calling start() and
    stop() directly. Can also be used as a context manager to time
    the body of the With block.
    """
    
    def __init__(self, timefunc=time.clock):
        self.timefunc = timefunc
        """Timing function. Must return a monotonically increasing
        numerical value.
        """
        
        self.running = False
        """Current state."""
        self.ticks = 0
        """Accumulated time value."""
        self.checkpoint = None
        """Most recent value from timerfunc."""
    
    # Invariant: Result = ticks + (current time - checkpoint)
    
    def start(self):
        """Start running. Must be currently stopped."""
        assert not self.running
        self.running = True
        t = self.timefunc()
        self.checkpoint = t
    
    @property
    def elapsed(self):
        """Return elapsed time, whether or not running."""
        if self.running:
            # Propagate most recent elapsed time to ticks.
            t = self.timefunc()
            self.ticks += t - self.checkpoint
            self.checkpoint = t
        return self.ticks
    
    def consume(self):
        """Return elapsed time and reset to 0, whether or not
        already running.
        """
        if self.running:
            t = self.timefunc()
            self.ticks += t - self.checkpoint
            self.checkpoint = t
        res = self.ticks
        self.ticks = 0
        return res
    
    def stop(self):
        """Stop running. Must be currently running."""
        t = self.timefunc()
        assert self.running
        self.ticks += t - self.checkpoint
        self.running = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


def on_battery_power():
    """Return True if the computer is known to be on battery power.
    On non-windows platforms, always returns False.
    """
    if sys.platform != 'win32':
        return False
    
    # Implementation code by Ben Hoyt, taken from
    #   http://stackoverflow.com/questions/6153860/in-python-how-can-i-detect-
    #   whether-the-computer-is-on-battery-power
    # Also see comment there about possible signedness bug.
    import ctypes
    from ctypes import wintypes
    
    class SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [
            ('ACLineStatus', wintypes.BYTE),
            ('BatteryFlag', wintypes.BYTE),
            ('BatteryLifePercent', wintypes.BYTE),
            ('Reserved1', wintypes.BYTE),
            ('BatteryLifeTime', wintypes.DWORD),
            ('BatteryFullLifeTime', wintypes.DWORD),
        ]
    
    SYSTEM_POWER_STATUS_P = ctypes.POINTER(SYSTEM_POWER_STATUS)
    
    GetSystemPowerStatus = ctypes.windll.kernel32.GetSystemPowerStatus
    GetSystemPowerStatus.argtypes = [SYSTEM_POWER_STATUS_P]
    GetSystemPowerStatus.restype = wintypes.BOOL
    
    status = SYSTEM_POWER_STATUS()
    if not GetSystemPowerStatus(ctypes.pointer(status)):
        raise ctypes.WinError()
    
    # 0: offline, 1: online, 255: unknown
    return status.ACLineStatus != 0


def get_mem_usage():
    """Return total process memory usage, in bytes.
    Requires Windows.
    """
    try:
        import psutil
    except ImportError:
        return 0
    process = psutil.Process(os.getpid())
    return process.get_memory_info().vms
