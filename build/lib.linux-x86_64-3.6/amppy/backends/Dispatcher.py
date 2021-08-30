from abc import ABC, abstractmethod
from pathlib import Path
import numpy as np
import enlighten
import threading
from enum import Enum
import os
from itertools import combinations
import pandas as pd
from colorama import Fore, Style, init
init()

class FitStatus(Enum):
    FAILED = 0
    CONVERGED = 1
    CALL_LIMIT = 2
    UNKNOWN = 3
    NO_FIT = 4

class ConvergenceCounter():
    def __init__(self, manager, total, name):
        fmt = '{desc}{desc_pad}{percentage:3.0f}%|{bar}|{count:{len_total}d}/{total:d}'
        self.total = manager.counter(total=total,
                                     color='green',
                                     desc=name,
                                     bar_format=fmt)
        self.call_limit = self.total.add_subcounter(color='yellow')
        self.failed = self.total.add_subcounter(color='red')

    def update(self, fit_status):
        if fit_status == FitStatus.FAILED:
            self.failed.update()
        elif fit_status == FitStatus.CALL_LIMIT:
            self.call_limit.update()
        elif fit_status == FitStatus.CONVERGED:
            self.total.update()


class Dispatcher(ABC):
   
    def __init__(self):
        self._root_directory = None
        self._config_template = None
        self._n_bins = None
        self._iterations = None
        self._reaction = None
        self._seed = None
        self._seed_list = None
        self._bootstrap = None
        self._bar_manager = enlighten.get_manager()
        self.status_bar = None #self._bar_manager.status_bar("DEFAULT", color='white_on_black', justify=enlighten.Justify.CENTER)
        self.total_counter = None
        self.bin_counters = None
        self._verbosity = None

    @property
    def root_directory(self):
        return self._root_directory

    @root_directory.setter
    def root_directory(self, path):
        if path.is_dir():
            self._root_directory = path
            bin_numbers, _ = self.get_bin_info()
            self.n_bins = len(bin_numbers)
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def config_template(self):
        return self._config_template

    
    @config_template.setter
    def config_template(self, path):
        if path.is_file():
            self._config_template = path
            self._reaction = "reaction not found"
            with open(path, 'r') as temp:
                lines = temp.readlines()
                for line in lines:
                    if line.startswith("reaction"):
                        self._reaction = line.split()[1]
            print(f"Reaction Name: {self.reaction}")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def n_bins(self):
        return self._n_bins

    @n_bins.setter
    def n_bins(self, n):
        assert n > 0, "Must have a positive number of bins"
        self._n_bins = n

    def get_bin_info(self):
        with open(self.root_directory / "bin_info.txt") as reader:
            lines = reader.readlines()
            bin_numbers = []
            bin_edges = []
            for line in lines[1:]:
                line = line.strip()
                bin_number, bin_edge = line.split("\t")
                bin_numbers += [bin_number]
                bin_edges += [bin_edge]
        return bin_numbers, bin_edges


    @property
    def bin_dirs(self):
        return [self.root_directory / str(n) for n in range(self.n_bins)]

    @property
    def iterations(self):
        return self._iterations

    @iterations.setter
    def iterations(self, i):
        assert i > 0, "Must have a positive number of iterations"
        self._iterations = i

    @property
    def reaction(self):
        return self._reaction

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, value):
        np.random.seed(value)
        self._seed = value
        self._seed_list = [np.random.randint(1, high=100000) for _ in range(self.iterations)]

    @property
    def seed_list(self):
        return self._seed_list


    def get_seed(self, iteration):
        return self.seed_list[iteration]


    @property
    def bootstrap(self):
        return self._bootstrap

    @bootstrap.setter
    def bootstrap(self, is_bootstrap):
        self._bootstrap = is_bootstrap

    @property
    def bar_manager(self):
        return self._bar_manager

    @property
    def verbosity(self):
        return self._verbosity

    @verbosity.setter
    def verbosity(self, level: int):
        self._verbosity = level

    @staticmethod
    @abstractmethod
    def dispatcher_description():
        pass

    @staticmethod
    @abstractmethod
    def add_arguments(parser):
        pass


    @abstractmethod
    def submit_jobs(self):
        pass


    def get_fit_results_files(self, bin_n, iteration):
        fit_file = (self.bin_dirs[bin_n] / str(iteration) / f"{self.config_template.stem}_{bin_n}::fit_results.txt").resolve()
        bootstrap_file = (self.bin_dirs[bin_n] / str(iteration) / f"{self.config_template.stem}_{bin_n}_bootstrap::fit_results.txt").resolve()
        return fit_file, bootstrap_file

    def get_fit_files(self, bin_n, iteration):
        fit_files = sorted(list((self.bin_dirs[bin_n] / str(iteration)).resolve().glob(f"{self.config_template.stem}_{bin_n}*.fit")), key=os.path.getmtime)
        bootstrap_files = sorted(list((self.bin_dirs[bin_n] / str(iteration)).resolve().glob(f"{self.config_template.stem}_{bin_n}_bootstrap*.fit")), key=os.path.getmtime)
        return fit_files, bootstrap_files

    def is_fit(self, bin_n, iteration):
        fit_file, bootstrap_file = self.get_fit_results_files(bin_n, iteration)
        if self.bootstrap:
            return bootstrap_file.exists()
        else:
            return fit_file.exists()


    def remove_fit(self, bin_n, iteration):
        fit_file, bootstrap_file = self.get_fit_results_files(bin_n, iteration)
        fit_amptools_files, bootstrap_amptools_files = self.get_fit_files(bin_n, iteration)
        if self.is_fit(bin_n, iteration):
            if not self.bootstrap:
                fit_file.unlink()
                if fit_amptools_files:
                    for f in fit_amptools_files:
                        if f.exists():
                            f.unlink()
            if bootstrap_file.exists():
                bootstrap_file.unlink()
            if bootstrap_amptools_files:
                for f in bootstrap_amptools_files:
                    if f.exists():
                        f.unlink()

    def remove_fits(self):
        for bin_n in range(self.n_bins):
            for iteration in range(self.iterations):
                self.remove_fit(bin_n, iteration)


    def get_fit_status(self, bin_n, iteration):
        fit_files, bootstrap_files = self.get_fit_files(bin_n, iteration)
        if self.bootstrap:
            if not bootstrap_files:
                return FitStatus.NO_FIT
            fit_file = bootstrap_files[0]
        else:
            if not fit_files:
                return FitStatus.NO_FIT
            fit_file = fit_files[0]
        if "FAILED" in fit_file.name:
            return FitStatus.FAILED
        elif "CONVERGED" in fit_file.name:
            return FitStatus.CONVERGED
        elif "CALL_LIMIT" in fit_file.name:
            return FitStatus.CALL_LIMIT
        else:
            return Fitstatus.UNKNOWN


    def get_active_jobs(self):
        return [[not self.is_fit(n, iteration) for iteration in range(self.iterations)] for n in range(self.n_bins)]


    def preprocessing(self, **kwargs):
        pass

    def postprocessing(self, **kwargs):
        pass

    def setup(self, root_directory: str, config_template: str, iterations: int, seed: int, bootstrap: bool, verbosity: int):
        self.root_directory = Path(root_directory).resolve()
        self.config_template = Path(config_template).resolve()
        self.iterations = iterations
        self.seed = seed
        self.bootstrap = bootstrap
        self.verbosity = verbosity

    def create_counters(self):
        active_jobs = self.get_active_jobs() # list of True if not fit
        active_indices = np.argwhere(active_jobs)
        if self.verbosity == 2:
            self.total_counter = ConvergenceCounter(self.bar_manager, len(active_indices), "Total")
            self.bin_counters = [ConvergenceCounter(self.bar_manager, len(np.argwhere(active_jobs[n])), f"Bin {n}" + " " * (4 - len(str(n)))) for n in range(self.n_bins)]
            self.status_bar = self.bar_manager.status_bar('Submitting Jobs', color='white_on_black', justify=enlighten.Justify.CENTER)
        elif self.verbosity == 1: # no bin counters
            self.total_counter = ConvergenceCounter(self.bar_manager, len(active_indices), "Total")
            self.status_bar = self.bar_manager.status_bar('Submitting Jobs', color='white_on_black', justify=enlighten.Justify.CENTER)

    @abstractmethod
    def update_status(self):
        pass

    def update_counters(self):
        active_jobs = self.get_active_jobs()
        active_indices = np.argwhere(active_jobs)
        while len(active_indices) != 0:
            for ind in active_indices:
                bin_n = ind[0]
                iteration = ind[1]
                fit_status = self.get_fit_status(bin_n, iteration)
                if fit_status != FitStatus.NO_FIT:
                    active_jobs[bin_n][iteration] = False
                    if self.bin_counters != None:
                        self.bin_counters[bin_n].update(fit_status)
                    if self.total_counter != None:
                        self.total_counter.update(fit_status)
                    active_indices = np.argwhere(active_jobs)
            self.update_status()


    def gather(self):
        amplitudes = []
        with open(self.config_template, 'r') as cfg:
            for line in cfg.readlines():
                if line.startswith("amplitude"):
                    amplitudes.append(line.split()[1].strip())
        headers = []
        for wave_name in amplitudes:
            wave_parts = wave_name.split("::")
            if wave_parts[1].endswith("Re"):
                headers.append(wave_parts[2] + "_NC_INT")
                headers.append(wave_parts[2] + "_NC_INT_err")
                headers.append(wave_parts[2] + "_AC_INT")
                headers.append(wave_parts[2] + "_AC_INT_err")
        for wave_name in amplitudes:
            wave_parts = wave_name.split("::")
            if wave_parts[1].endswith("Re"):
                headers.append(wave_parts[2] + "_AMP")
        wave_pairs = combinations(amplitudes, 2)
        for wave_pair in wave_pairs:
            wave_name1, wave_name2 = wave_pair
            wave_parts1 = wave_name1.split("::")
            wave_parts2 = wave_name2.split("::")
            if wave_parts1[1].endswith("Re") and wave_parts2[1].endswith("Re"):
                if wave_parts1[1] == wave_parts2[1]:
                    headers.append(wave_parts1[2] + "_" + wave_parts2[2] + "_PHASE")  
                    headers.append(wave_parts1[2] + "_" + wave_parts2[2] + "_PHASE_err")  
        headers.append("total_NC_INT")
        headers.append("total_NC_INT_err")
        headers.append("total_AC_INT")
        headers.append("total_AC_INT_err")
        headers.append("likelihood")
        if self.bootstrap:
            output_file_name = self.config_template.stem + "_bootstrap::fit_results.txt"
        else:
            output_file_name = self.config_template.stem + "::fit_results.txt"
        with open(self.root_directory / output_file_name, 'w') as out_file:
            header = "\t".join(headers)
            out_file.write(f"Bin\tIteration\tConvergence\t{header}\n")
            bin_converged_total = np.zeros_like(self.bin_dirs)
            bin_total = np.ones_like(self.bin_dirs) * self.iterations
            for bin_n in range(self.n_bins):
                for iteration in range(self.iterations):
                    fit_results, bootstrap_results = self.get_fit_results_files(bin_n, iteration)
                    if self.bootstrap:
                        fit_results = bootstrap_results
                    converged = "U"
                    if fit_results.exists():
                        with open(fit_results, 'r') as fit_res:
                            line = fit_res.readline()
                            if line != "":
                                converged = line.split('\t')[2].strip()
                                out_file.write(line)
                        if converged == "C":
                            bin_converged_total[bin_n] += 1
        print("Convergence Results:")
        for bin_n in range(self.n_bins):
            percent_converged = bin_converged_total[bin_n] / bin_total[bin_n]
            if percent_converged == 0:
                color = Fore.RED
            elif percent_converged <= 0.25:
                color = Fore.YELLOW
            elif percent_converged <= 0.80:
                color = Fore.BLUE
            else:
                color = Fore.GREEN
            print(f"{color}Bin {bin_n}: {bin_converged_total[bin_n]}/{bin_total[bin_n]}\t{Style.RESET_ALL}", end='')
        print()

    
    def bootstrap_config(self):
        df = pd.read_csv(self.root_directory / f"{self.config_template.stem}::fit_results.txt",
                         delimiter="\t",
                         index_col=False)
        best_fit = df.loc[df.groupby(['Bin'])['likelihood'].idxmax()].set_index('Bin')
        for bin_n in range(self.n_bins):
            bin_config = self.bin_dirs[bin_n] / f"{self.config_template.stem}_{bin_n}.cfg"
            bin_config_dest = self.bin_dirs[bin_n] / f"{self.config_template.stem}_{bin_n}_bootstrap.cfg"
            with open(bin_config, 'r') as config_old:
                config_old_lines = config_old.readlines()
            with open(bin_config_dest, 'w') as config_bootstrap:
                for line in config_old_lines:
                    if "ROOTDataReader" in line:
                        line = line.replace("ROOTDataReader", "ROOTDataReaderBootstrap")
                        line = line.replace("\n", " @seed\n")
                    if line.startswith("initialize"):
                        line = line.replace("polar", "cartesian")
                        wave_name = line.split(" ")[1].split("::")[2]
                        fields = line.split(" ")
                        fields[3] = str(complex(best_fit.iloc[bin_n][wave_name + "_AMP"]).real)
                        fields[4] = str(complex(best_fit.iloc[bin_n][wave_name + "_AMP"]).imag)
                        line = " ".join(fields)
                        line += "\n"
                    config_bootstrap.write(line)


    def dispatch(self, **kwargs):
        self.preprocessing(**kwargs)
        if self.bootstrap:
            self.bootstrap_config()
        if self.verbosity > 0:
            self.create_counters()
            counters = threading.Thread(target=update_counter_thread, args=(self,))
            counters.start()
            self.submit_jobs()
            self.postprocessing(**kwargs)
            counters.join()
            self.bar_manager.stop()
            self.gather()
        else:
            self.submit_jobs()
            self.postprocessing(**kwargs)
            self.gather()


def update_counter_thread(disp):
    disp.update_counters()
