"""Ensure that the output produced by each test program is identical."""


from copy import deepcopy
import pickle
import gc
from itertools import groupby

from frexp.driver import Driver
from frexp.runner import Runner


def canonize(tree):
    """Recursively convert helper types into standard Python types.
    The tree may consist of the following types:
    
      Python types (left as-is):
        - None, ints, floats, strings
        - lists, sets, dicts, tuples
      
      runtimelib types:
        - Set and RCSet get replaced by Python sets
        - Obj gets replaced by a frozenset of key/value tuples
          from its __dict__, excluding attributes that begin with one
          or more underscores
      
      osq types:
        - RCSet gets replaced by a Python set
    
    Aliasing is not preserved.
    
    The purpose of this function is to create a nearly semantically
    equivalent value that can be compared for equality with other
    values. This is needed because the transformed program uses
    helper types that are similar to, but not identical to, their
    corresponding basic Python types.
    """
    import runtimelib
    import osq
    
    if isinstance(tree, (runtimelib.Set, runtimelib.RCSet, osq.incr.RCSet)):
        result = set(canonize(v) for v in tree)
    
    elif isinstance(tree, runtimelib.Obj):
        result = frozenset((canonize(k), canonize(v))
                           for k, v in tree.__dict__.items()
                           if not k.startswith('_'))
    
    elif isinstance(tree, (type(None), int, float, str, bool)):
        result = tree
    
    elif isinstance(tree, (list, set, tuple)):
        result = type(tree)(canonize(v) for v in tree)
    
    elif isinstance(tree, dict):
        result = type(tree)(canonize(v) for v in tree.items())
    
    else:
        raise ValueError('Un-canonizable type: ' + str(type(tree)))
    
    assert not type(result).__module__ in ['runtimelib.runtimelib', 'osq.incr']
    
    return result


class VerifyDriver(Driver):
    
    """Instead of recording test metrics like time and space, record
    the metric of program output. Specifically, record the values
    returned by operations. Value types must be picklable.
    """
    
    def sanitize(self, tree):
        """Turn an operation return value into something safe to
        store and compare.
        """
        # Convert runtimelib types back to Python types if possible,
        # for equality comparison purposes. Deepcopy just to be
        # super safe in avoiding hard-to-track bugs, although it
        # shouldn't be necessary because canonize() makes a copy.
        tree = canonize(tree)
        tree = deepcopy(tree)
        return tree
    
    def execute_ops(self):
        """Record a single metric: output, as a string."""
        res = {}
        
        init_seqdata = {'output': []}
        
        for opseq in self.opseqs:
            ops = opseq['ops']
            reps = opseq['reps']
            for _ in range(reps):
                for op in ops:
                    seq_name, func, *args = op
                    
                    if seq_name == 'GET_SPACE_USAGE':
                        continue
                    
                    seq_data = res.setdefault(seq_name, deepcopy(init_seqdata))
                    
                    r = func(*args)
                    r = self.sanitize(r)
                    
                    seq_data['output'].append(r)
        
        self.result_data = {}
        self.result_data['seqs'] = res
        self.result_data['sizes'] = {}
        self.result_data['memory'] = 0


class Verifier(Runner):
    
    """Similar to the standard Runner, but do comparison work as
    each test result comes back and stop at the first failure.
    """
    
    # At any given time, we only hold onto the current test result
    # and the one we're trying to match it to. This avoids consuming
    # more memory as the number of tests increases, and it also avoids
    # additional unnecessary serialization work.
    
    # TODO: If it turns out that equality comparison among large sets
    # ends up being a limiting factor, we can turn this into a hash-
    # based or sort-based equality. This would probably require a
    # recursive traversal, similar to how canonization is done. 
    
    @property
    def drivermain(self):
        return main
    
    def run_all_tests(self, tparams_list):
        """Run all tests."""
        
        # Group trials by dataset id.
        tparams_list.sort(key=lambda t: t['dsid'])
        groups = groupby(tparams_list, key=lambda t: t['dsid'])
        
        current = 0
        total = len(tparams_list)
        for dsid, tparams_sublist in groups:
            goal = None
            
            for trial in tparams_sublist:
                current += 1
                self.print('Verifying test {} of {} '
                           '...'.format(current, total))
                datapoint = self.run_single_test(trial)
                if goal is None:
                    goal = datapoint['results']
                else:
                    if goal != datapoint['results']:
                        self.print('Output disagrees for dataset ' +
                                   str(dsid))
                        self.print('  params: ' + str(datapoint['dsparams']))
                        return
        
        print('Output agrees on all datasets.')
        return
    
    def run(self):
        with open(self.in_filename, 'rb') as in_file:
            tparams_list = pickle.load(in_file)
        
        self.run_all_tests(tparams_list)
        
        self.print('Done.')


def main(pipe_filename):
    gc.disable()
    
    with open(pipe_filename, 'rb') as pf:
        dataset, prog = pickle.load(pf)
    
    driver = VerifyDriver(dataset, prog)
    results = driver.run()
    
    with open(pipe_filename, 'wb') as pf:
        pickle.dump(results, pf)
