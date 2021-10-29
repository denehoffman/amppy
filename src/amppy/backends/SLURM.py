from amppy.backends.Dispatcher import Dispatcher
import subprocess
from pathlib import Path
import time
import os
import numpy as np

class SLURM(Dispatcher):
    @staticmethod
    def dispatcher_description():
        return ("CMU_SLURM", "SLURM dispatcher for the CMU MEG cluster")

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--queue", choices=["red", "green", "blue"], help="select which queue to use", default="red")

    def preprocessing(self, **kwargs):
        self.queue = str(kwargs.get("queue"))
        self.threads = 4
        if self.queue == "green":
            self.cpu_memory = 1590
        elif self.queue == "red":
            self.cpu_memory = 1990

    def postprocessing(self, **kwargs):
        while np.any(self.get_active_jobs()):
            time.sleep(5)

    def update_status(self):
        username = os.getlogin()
        n_jobs_queued = len(subprocess.run(['squeue', '-h', '-u', username], stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines())
        n_jobs_running = len(subprocess.run(['squeue', '-h', '-u', username, '-t', 'running'], stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines())
        self.status_bar.update(f"{n_jobs_queued - n_jobs_running} job(s) currently queued, {n_jobs_running} job(s) running")
        time.sleep(1)


    def submit_jobs(self):
        for bin_num, bin_dir in enumerate(self.bin_dirs):
            for iteration in range(self.iterations):
                if not self.is_fit(bin_num, iteration):
                    slurm_args = ["sbatch",
                                  f"--job-name={self.reaction}_{bin_dir.name}_{iteration}",
                                  f"--ntasks={self.threads}",
                                  f"--partition={self.queue}",
                                  f"--mem={self.cpu_memory * self.threads}",
                                  f"--time=1:00:00",
                                  "--quiet"]
                    slurm_command = ["sbatch_job.csh"]
                    command_args = [str(bin_dir),
                                    str(bin_num),
                                    str(iteration),
                                    str(self.get_seed(iteration)),
                                    str(self.reaction),
                                    str(self.bootstrap),
                                    str(self.config_template)]
                    r = subprocess.run(slurm_args + slurm_command + command_args, stdout=subprocess.PIPE)
                    time.sleep(1)
