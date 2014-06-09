"""Run the driver program multiple times and aggregate the results."""


__all__ = [
    'Runner',
]


import pickle
import os
from multiprocessing import Process

import numpy as np

from frexp.util import on_battery_power
from frexp.workflow import Task


class Runner(Task):
    
    """Test runner."""
    
    show_time = True
    
    # Each invocation of the driver is done as a separate process,
    # so that there is no chance of contamination between tests.
    
    ### TODO: Optimize to pass in dsid directly to child,
    ### instead of copying from ds file to pipe.
    
    def dispatch_test(self, dataset, prog, other_tparams):
        """Spawn a driver process and get its result."""
        # Communicate the dataset and results via a temporary
        # pipe file.
        pipe_fn = self.workflow.pipe_filename
        with open(pipe_fn, 'wb') as pf:
            pickle.dump((dataset, prog, other_tparams), pf)
        
        child = Process(target=self.workflow.ExpDriver, args=(pipe_fn,))
        child.start()
        
        child.join()
        if child.exitcode != 0:
            raise ValueError('Child failed with exit code ' +
                             str(child.exitcode))
        with open(pipe_fn, 'rb') as pf:
            results = pickle.load(pf)
        
        os.remove(pipe_fn)
        return results
    
    def run_single_test(self, trial):
        """Run a single execution and return its result datapoint."""
        trial = dict(trial)
        dsid = trial.pop('dsid')
        prog = trial.pop('prog')
        
        ds_fn = self.workflow.get_ds_filename(dsid)
        with open(ds_fn, 'rb') as dsfile:
            dataset = pickle.load(dsfile)
        
        results = self.dispatch_test(dataset, prog, trial)
        
        datapoint = {'dsparams': dataset['dsparams'],
                     'prog': prog,
                     'results': results}
        datapoint.update(trial)
        return datapoint
    
    def repeat_single_test(self, trial, itemstrlen):
        """Repeatedly run a trial until it meets the standard
        deviation and min-repeats requirements, as measured
        by 'all' seq process time. Return all datapoints.
        """
        if not self.workflow.do_repeats:
            self.print()
            return [self.run_single_test(trial)]
        
        else:
            self.print('  ', end='')
            datapoints = []
            times = []
            
            timedout = False
            
            min = self.workflow.min_repeats
            max = self.workflow.max_repeats
            window = self.workflow.stddev_window
            def stabilized():
                m = np.mean(times)
                s = np.std(times)
                if m < self.workflow.repeat_ylimit:
                    return True
                return s / m <= window if m > 0 else True
            
            while (len(times) == 0 or       # first time
                   len(times) < min or      # didn't reach min
                   (len(times) < max and    # can do more trials
                    not stabilized())):        # should do more trials
                if len(times) > 0 and len(times) % 10 == 0:
                    statusstr = '  ({:.3f}, {:.3f})'.format(
                                np.std(times), np.mean(times))
                    statusstr = statusstr.ljust(itemstrlen)
                    self.print('\n' + statusstr, end='')
                self.print('. ', end='')
                dp = self.run_single_test(trial)
                
                if 'timedout' in dp['results'] and dp['results']['timedout']:
                    timedout = True
                    break
                
                datapoints.append(dp)
                times.append(dp['results']['stdmetric'])
            
            if timedout:
                if len(datapoints) > 0:
                    self.print('Warning: Discarding trials due to timeout')
                else:
                    self.print('Timed out')
                
            elif len(times) == max and not stabilized():
                self.print('Warning: Did not converge '
                           '(std={}, mean={})'.format(
                           np.std(times), np.mean(times)))
            self.print()
            
            return datapoints, timedout
    
    def run_all_tests(self, tparams_list):
        """Run all test trials."""
        datapoint_list = []
        for i, trial in enumerate(tparams_list, 1):
            itemstr = 'Running test {} of {} ...'.format(i, len(tparams_list))
            self.print(itemstr, end='')
            datapoints, _timedout = self.repeat_single_test(
                                                trial, len(itemstr))
            datapoint_list.extend(datapoints)
        return datapoint_list
    
    def run(self):
        if self.workflow.require_ac and on_battery_power():
            raise AssertionError('AC Power required for benchmarking')
        
        with open(self.workflow.params_filename, 'rb') as in_file:
            tparams_list = pickle.load(in_file)
        
        datapoint_list = self.run_all_tests(tparams_list)
        
        out_fn = self.workflow.data_filename
        self.print('Writing to ' + out_fn)
        with open(out_fn, 'wb') as out_file:
            pickle.dump(datapoint_list, out_file)
        
        self.print('Done.')
    
    def cleanup(self):
        self.remove_file(self.workflow.data_filename)
        self.remove_file(self.workflow.pipe_filename)
