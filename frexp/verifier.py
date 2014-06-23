"""Ensure that the output produced by each test program is identical."""


__all__ = [
    'Verifier',
]


import pickle
from itertools import groupby
from operator import itemgetter
import os
from multiprocessing import Process

from frexp.workflow import Task


class Verifier(Task):
    
    """Run each test once and ensure that different progs agree
    on the results.
    """
    
    # At any given time, we only hold onto the current test result
    # and the one we're trying to match it to. This avoids consuming
    # more memory as the number of tests increases, and it also avoids
    # additional unnecessary serialization work.
    
    # TODO: If it turns out that equality comparison among large sets
    # ends up being a limiting factor, we can turn this into a hash-
    # based or sort-based equality. This would probably require a
    # recursive traversal, similar to how canonization is done. 
    
    # Copied from Runner, should refactor.
    
    def dispatch_test(self, dataset, prog, other_tparams):
        """Spawn a driver process and get its result."""
        # Communicate the dataset and results via a temporary
        # pipe file.
        pipe_fn = self.workflow.pipe_filename
        with open(pipe_fn, 'wb') as pf:
            pickle.dump((dataset, prog, other_tparams), pf)
        
        child = Process(target=self.workflow.ExpVerifyDriver, args=(pipe_fn,))
        child.start()
        
        child.join()
        with open(pipe_fn, 'rb') as pf:
            results = pickle.load(pf)
        
        os.remove(pipe_fn)
        return results
    
    def run(self):
        with open(self.workflow.params_filename, 'rb') as in_file:
            tparams_list = pickle.load(in_file)
        
        with open(self.workflow.data_filename, 'rb') as in_file:
            datapoints = pickle.load(in_file)
        datapoint_tids = set(d['tid'] for d in datapoints)
        
        tparams_list.sort(key=itemgetter('tid'))
        tgroups = groupby(tparams_list, itemgetter('tid'))
        tgroups = [(tid, list(tgs)) for tid, tgs in tgroups]
        
        for i, (tid, tgs) in enumerate(tgroups):
            if tid not in datapoint_tids:
                print('Skipping trial group {:<10} ({}/{})\n  '.format(
                      tid + ' ...', i, len(tgroups)))
            
            itemstr = 'Verifying trial group {:<10} ({}/{})\n  '.format(
                        tid + ' ...', i, len(tgroups))
            self.print(itemstr, end='')
            goal = None
            goalprog = None
            for trial in tgs:
                trial = dict(trial)
                dsid = trial.pop('dsid')
                prog = trial.pop('prog')
                
                self.print(prog, end='  ')
                
                ds_fn = self.workflow.get_ds_filename(dsid)
                with open(ds_fn, 'rb') as dsfile:
                    dataset = pickle.load(dsfile)
                
                output = self.dispatch_test(dataset, prog, trial)['output']
                
                if goal is None:
                    goal = output
                    goalprog = prog
                else:
                    if output != goal:
                        self.print()
                        self.print('Output disagrees for trial group ' + tid)
                        self.print('  params: ' + str(dataset['dsparams']))
                        self.print('  goalprog: {}, prog: {}'.format(
                                   goalprog, prog))
                        return
            
            self.print()
        
        self.print('Output agrees on all datasets.')
        self.print('Done.')
