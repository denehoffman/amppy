from amppy.backends.Dispatcher import Dispatcher
from amppy.backends.Fitter import Fitter
from multiprocessing import Pool
import subprocess
import time

def run_pool(tup):
    bin_dir, bin_num, iteration, seed, reaction, bootstrap, config_template = tup
    f = Fitter()
    f.setup(bin_dir, bin_num, iteration, seed, reaction, bootstrap, config_template)
    f.fit()

class PythonMultiprocessing(Dispatcher):
    
    @staticmethod
    def dispatcher_description():
        return ("Pool", "Python's native multiprocessing")

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("-p", "--processes", type=int, help="number of processes to generate", default=5)

    def preprocessing(self, **kwargs):
        self.processes = kwargs.get("processes")
        assert self.processes > 0

    
    def update_status(self):
        self.status_bar.update(f"Submitting using Python Multiprocessing Pool with {self.processes} process(es)")

    
    def submit_jobs(self):
        input_tups = [(self.bin_dirs[bin_num], bin_num, iteration, self.get_seed(iteration), self.reaction, self.bootstrap, self.config_template) for bin_num in range(self.n_bins) for iteration in range(self.iterations)]
        with Pool(processes=self.processes) as pool:
            p = pool.map(run_pool, input_tups)
        print("Done!")
