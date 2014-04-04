"""Execute a test, running and benchmarking the given operations.

This is intended to be executed as a child process using the
multiprocessing library. For each driver class there is a
corresponding global main() function that calls it. This is
because even a class method would be unpicklable and hence
uncallable by multiprocessing.

The main() function receives the name of a temporary file in
which it receives the dataset and sends back the results.
"""


__all__ = [
    'Driver',
    'IndvDriver',
    'AllDriver',
]


import sys
import gc
import os
import pickle
import importlib
from time import perf_counter, process_time

from .util import StopWatch, get_mem_usage


def user_time():
    return os.times()[0]


class Driver:
    
    """Encapsulates everything needed to run a driven program."""
    
    def __init__(self, dataset, prog):
        self.dataset = dataset
        """Test data read in as input."""
        self.prog = prog
        """Driven program's module name."""
        self.module = None
        """Driven program's module."""
        self.opseqs = []
        """Operations to execute and measure. Format of each item:
        
            {'ops': (seq name, func, *args),
             'reps: <int>}
        """
    
    def run(self):
        self.import_program()
        self.import_data()
        self.execute_ops()
        return self.result_data
    
    def import_program(self):
        """Import the driven program's module."""
        # The best way I know of importing from a directory is to
        # temporarily add the directory to sys.path. I doubt this is
        # Pythonic, since it's not thread-safe, etc., but it's
        # easy and it works.
        dirname, filename = os.path.split(self.prog)
        
        if dirname:
            sys.path.append(dirname)
        try:
            self.module = importlib.import_module(filename)
        finally:
            if dirname:
                sys.path.pop()
    
    def import_data(self):
        """Read the test data into an internal format. Namely, replace
        operation names with their actual function references, and
        replace value ids with actual Set/Obj values.
        """
        values = self.dataset['values']
        
        typemap = {'Set': self.module.Set,
                   'Obj': self.module.Obj}
        value_store = {id: typemap[t]() for id, t in values}
        
        # Normalize ops to opseqs.
        if 'ops' in self.dataset:
            opseqs = [{'ops': self.dataset['ops'],
                       'reps': 1}]
        else:
            opseqs = self.dataset['opseqs']
        
        for opseq in opseqs:
            ops = opseq['ops']
            norm_ops = []
            for op in ops:
                seq_name, func_name, *pre_args = op
                func = (getattr(self.module, func_name)
                        if func_name is not None else None)
                args = [value_store.get(arg, arg)
                        for arg in pre_args]
                tup = tuple([seq_name, func] + args)
                norm_ops.append(tup)
            self.opseqs.append({'ops': norm_ops,
                                'reps': opseq['reps'],
                                'timed': opseq['timed']})
    
    def execute_ops(self):
        """Run and benchmark each of the operation sequences."""
        raise NotImplementedError


class IndvDriver(Driver):
    
    """Driver that times each operation individually."""
    
    def execute_ops(self):
        import runtimelib
        
        # Currently the available metrics are:
        #   total time, as measured by process time and wall time
        self.result_data = {}
        self.result_data['seqs'] = {}
        self.result_data['sizes'] = {}
        self.result_data['memory'] = 0
        
        res = {}
        
        init_seqdata = {'numops': 0,
                        'time_user': 0,
                        'time_cpu': 0,
                        'time_wall': 0}
        
        timer_user = StopWatch(user_time)
        timer_cpu = StopWatch(process_time)
        timer_wall = StopWatch(perf_counter)
        
        for opseq in self.opseqs:
            ops = opseq['ops']
            reps = opseq['reps']
            for _ in range(reps):
                for op in ops:
                    seq_name, func, *args = op
                    
                    # Semi-hackish way of supporting space usage:
                    # When we see this magic string, update the result's
                    # space usage (should only occur once; delete any
                    # previous entry) instead of timing something.
                    if seq_name == 'GET_SPACE_USAGE':
                        self.result_data['sizes'] = runtimelib.get_structure_sizes()
                        self.result_data['memory'] = get_mem_usage()
                    
                    else:
                        seq_data = res.setdefault(seq_name, init_seqdata.copy())
                        
                        with timer_user, timer_cpu, timer_wall:
                            func(*args)
                        
                        seq_data['numops'] += 1
                        seq_data['time_user'] += timer_user.consume()
                        seq_data['time_cpu'] += timer_cpu.consume()
                        seq_data['time_wall'] += timer_wall.consume()
        
        for seq_name, seq_data in res.items():
            self.result_data['seqs'][seq_name] = {
                'ttltime_user': seq_data['time_user'],
                'ttltime_cpu': seq_data['time_cpu'],
                'ttltime_wall': seq_data['time_wall'],
            }


class AllDriver(Driver):
    
    """Driver that times all operations together as a single sequence."""
    
    def import_data(self):
        super().import_data()
        # Get rid of the space usage op.
        for opseq in self.opseqs:
            opseq['ops'] = [op for op in opseq['ops']
                               if op[0] != 'GET_SPACE_USAGE']
    
    def execute_ops(self):
        import runtimelib
        
        # Currently the available metrics are:
        #   average and total time, as measured by wall time and
        #   process time
        self.result_data = {}
        self.result_data['seqs'] = {}
        self.result_data['sizes'] = {}
        self.result_data['memory'] = 0
        
        res = {}
        
        init_seqdata = {'numops': 0,
                        'time_user': 0,
                        'time_cpu': 0,
                        'time_wall': 0}
        
        timer_user = StopWatch(user_time)
        timer_cpu = StopWatch(process_time)
        timer_wall = StopWatch(perf_counter)
        
        seq_data = res.setdefault('all', init_seqdata.copy())
        
        for opseq in self.opseqs:
            timed = opseq['timed']
            if timed:
                timer_user.start()
                timer_cpu.start()
                timer_wall.start()
            
            ops = opseq['ops']
            reps = opseq['reps']
            for _ in range(reps):
                for op in ops:
                    seq_name, func, *args = op
                    func(*args)
            
            if timed:
                timer_user.stop()
                timer_cpu.stop()
                timer_wall.stop()
        
        seq_data['time_user'] = timer_user.elapsed
        seq_data['time_cpu'] = timer_cpu.elapsed
        seq_data['time_wall'] = timer_wall.elapsed
        
        self.result_data['sizes'] = runtimelib.get_structure_sizes()
        self.result_data['memory'] = get_mem_usage()
        
        for seq_name, seq_data in res.items():
            self.result_data['seqs'][seq_name] = {
                'ttltime_user': seq_data['time_user'],
                'ttltime_cpu': seq_data['time_cpu'],
                'ttltime_wall': seq_data['time_wall'],
            }


def main_indv(pipe_filename):
    gc.disable()
    
    with open(pipe_filename, 'rb') as pf:
        dataset, prog = pickle.load(pf)
    
    driver = IndvDriver(dataset, prog)
    results = driver.run()
    
    with open(pipe_filename, 'wb') as pf:
        pickle.dump(results, pf)


def main_all(pipe_filename):
    gc.disable()
    
    with open(pipe_filename, 'rb') as pf:
        dataset, prog = pickle.load(pf)
    
    driver = AllDriver(dataset, prog)
    results = driver.run()
    
    with open(pipe_filename, 'wb') as pf:
        pickle.dump(results, pf)
