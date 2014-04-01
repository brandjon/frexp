"""Run the driver program multiple times and aggregate the results."""


import pickle
import os
from multiprocessing import Process

from frexp.util import on_battery_power
from frexp.workflow import Task
from frexp import driver


class Runner(Task):
    
    """Test runner."""
    
    show_time = True
    
    # Each invocation of the driver is done as a separate process,
    # so that there is no chance of contamination between tests.
    
    # This has saved me countless times from accidentally running
    # tests on power-saving procesor speed.
    require_ac = True
    
    @property
    def drivermain(self):
        """Return the function to call in the child process to begin
        the driver. Must be pickleable.
        """
        return driver.main
    
    ### TODO: Optimize to pass in dsid directly to child,
    ### instead of copying from ds file to pipe.
    
    def dispatch_test(self, dataset, prog):
        """Spawn a driver process and get its result."""
        # Communicate the dataset and results via a temporary
        # pipe file.
        pipe_fn = self.workflow.pipe_filename
        with open(pipe_fn, 'wb') as pf:
            pickle.dump((dataset, prog), pf)
        
        child = Process(target=self.drivermain, args=(pipe_fn,))
        child.start()
        
        child.join()
        with open(self.pipe_filename, 'rb') as pf:
            results = pickle.load(pf)
        
        os.remove(self.pipe_filename)
        return results
    
    def run_single_test(self, trial):
        """Run a single execution and return its result datapoint."""
        dsid = trial['dsid']
        prog = trial['prog']
        
        ds_fn = self.workflow.get_ds_filename(dsid)
        with open(ds_fn, 'rb') as dsfile:
            dataset = pickle.load(dsfile)
        
        results = self.dispatch_test(dataset, prog)
        
        datapoint = {'dsparams': dataset['dsparams'],
                     'prog': prog,
                     'results': results}
        return datapoint
    
    def run_all_tests(self, tparams_list):
        """Run all test trials."""
        datapoint_list = []
        for i, trial in enumerate(tparams_list, 1):
            self.print('Running test {} of {} '
                       '...'.format(i, len(tparams_list)))
            datapoint = self.run_single_test(trial)
            datapoint_list.append(datapoint)
        return datapoint_list
    
    def run(self):
        if self.require_ac and on_battery_power():
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
