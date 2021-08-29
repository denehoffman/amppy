import numpy as np
import errno
import sys
import os
import subprocess
from amppy.fitresults import FitResults
from itertools import combinations
from pathlib import Path

class Fitter():
    
    def __init__(self):
        self._seed = None
        self._config = None
        self._config_template = None
        self._iteration = None
        self._bin_number = None
        self._reaction = None
        self._bootstrap = None
        self._bin_directory = None
        self._iteration_directory = None
        

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, value):
        np.random.seed(value)
        self._seed = value

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, path):
        if path.exists():
            self._config = path
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def config_template(self):
        return self._config_template

    @config_template.setter
    def config_template(self, path):
        if self.bootstrap:
            bin_path = self.bin_directory / (path.stem + f"_{self.bin_number}_bootstrap.cfg")
        else:
            bin_path = self.bin_directory / (path.stem + f"_{self.bin_number}.cfg")
        if bin_path.exists():
            self._config_template = bin_path
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(bin_path))

    @property
    def iteration(self):
        return self._iteration
    
    @iteration.setter
    def iteration(self, it):
        self._iteration = it

    @property
    def bin_number(self):
        return self._bin_number

    @bin_number.setter
    def bin_number(self, n):
        self._bin_number = n

    @property
    def reaction(self):
        return self._reaction

    @reaction.setter
    def reaction(self, name):
        self._reaction = name

    @property
    def bootstrap(self):
        return self._bootstrap

    @bootstrap.setter
    def bootstrap(self, boolean):
        self._bootstrap = boolean


    @property
    def bin_directory(self):
        return self._bin_directory

    @bin_directory.setter
    def bin_directory(self, path):
        if path.is_dir():
            self._bin_directory = path
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))


    @property
    def iteration_directory(self):
        return self._iteration_directory

    @iteration_directory.setter
    def iteration_directory(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._iteration_directory = path


    def create_config(self):
        with open(self.config_template, 'r') as config_temp:
            temp_lines = config_temp.readlines()
        new_config_path = self.iteration_directory / (self.config_template.stem + f"-{self.iteration}.cfg")
        with open(new_config_path, 'w') as new_config:
            output_lines = []
            for line in temp_lines:
                if '@seed' in line:
                    bootstrap_seed = str(np.random.randint(1, high=100000))
                    line = line.replace('@seed', bootstrap_seed)
                if line.startswith('initialize'):
                    line_parts = line.split()
                    if line_parts[2] == 'cartesian':
                        if line_parts[3] == '@uniform':
                            line_parts[3] = str(np.random.uniform(low=-100.0, high=100.0))
                        if line_parts[4] == '@uniform':
                            line_parts[4] = str(np.random.uniform(low=-100.0, high=100.0))
                    elif line_parts[2] == 'polar':
                        if line_parts[3] == '@uniform':
                            line_parts[3] = str(np.random.uniform(low=0.0, high=100.0))
                        if line_parts[4] == '@uniform':
                            line_parts[4] = str(np.random.uniform(low=0.0, high=2 * np.pi))
                    line = " ".join(line_parts)
                    line += "\n"
                output_lines.append(line)
            new_config.writelines(output_lines)
        self.config = new_config_path


    def setup(self, bin_directory: Path, bin_number: int, iteration: int, seed: int, reaction: str, bootstrap: bool, config_template: Path):
        self.bin_number = bin_number
        self.iteration = iteration
        self.seed = seed # sets seed
        self.reaction = reaction
        self.bootstrap = bootstrap
        self.bin_directory = bin_directory
        self.config_template = config_template
        self.iteration_directory = self.bin_directory / str(iteration)
        self.create_config()

    def fit(self):
        os.chdir(self.iteration_directory)
        process = subprocess.run(['fit', '-c', str(self.config)],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        fit_result = process.stdout
        if "STATUS=CONVERGED" in fit_result:
            status = "CONVERGED"
            convergence = "C"
        elif "STATUS=FAILED" in fit_result:
            status = "FAILED"
            convergence = "F"
        elif "STATUS=CALL LIMIT" in fit_result:
            status = "CALL_LIMIT"
            convergence = "L"
        else:
            status = "UNKNOWN"
            convergence = "U"
        fit_output_source = Path(self.reaction + ".fit").resolve()
        if self.bootstrap:
            fit_output_destination = Path(self.config_template.stem +
                                          "::" + fit_output_source.stem +
                                          f"::{status}.bootstrap").resolve()
        else:
            fit_output_destination = Path(self.config_template.stem +
                                          "::" + fit_output_source.stem +
                                          f"::{status}.fit").resolve()
        fit_output_source.replace(fit_output_destination)
        amplitudes = []
        polarizations = []
        with open(self.config, 'r') as cfg:
            for line in cfg.readlines():
                if line.startswith("amplitude"):
                    amplitudes.append(line.split()[1].strip())
                if line.startswith("define polAngle"):
                    polarizations.append(line.split()[1].replace("polAngle", ""))
        data_output_list = []
        wrapper = FitResults.FitResultsWrapper(str(fit_output_destination))
        for wave_name in amplitudes:
            waves = []
            wave_parts = wave_name.split("::")
            if wave_parts[1].endswith("Re"):
                for pol in polarizations:
                    waves.append(wave_parts[0] + pol + "::" + wave_parts[1] + "::" + wave_parts[2])
                    waves.append(wave_parts[0] + pol + "::" + wave_parts[1].replace("Re", "Im") + "::" + wave_parts[2])
                data_output_list.extend(wrapper.intensity(waves, False))
                data_output_list.extend(wrapper.intensity(waves, True))
        for wave_name in amplitudes:
            wave_parts = wave_name.split("::")
            if wave_parts[1].endswith("Re"):
                wave = wave_parts[0] + polarizations[0] + "::" + wave_parts[1] + "::" + wave_parts[2]
                data_output_list.append(wrapper.productionParameter(wave))
        wave_pairs = combinations(amplitudes, 2)
        for wave_pair in wave_pairs:
            wave_name1, wave_name2 = wave_pair
            wave_parts1 = wave_name1.split("::")
            wave_parts2 = wave_name2.split("::")
            if wave_parts1[1].endswith("Re") and wave_parts2[1].endswith("Re"):
                if wave_parts1[1] == wave_parts2[1]:
                    wave1 = wave_parts1[0] + polarizations[0] + "::" + wave_parts1[1] + "::" + wave_parts1[2]
                    wave2 = wave_parts2[0] + polarizations[0] + "::" + wave_parts2[1] + "::" + wave_parts2[2]
                    data_output_list.extend(wrapper.phaseDiff(wave1, wave2))
        data_output_list.extend(wrapper.total_intensity(False))
        data_output_list.extend(wrapper.total_intensity(True))
        data_output_list.append(wrapper.likelihood())
        if self.bootstrap:
            output_file_name = self.config_template.stem + "::bootstrap.txt"
        else:
            output_file_name = self.config_template.stem + "::fit_results.txt"
        with open(output_file_name, 'w') as out_file:
            if convergence == 'C' or convergence == 'L':
                output = "\t".join([str(itm) for itm in data_output_list])
                out_file.write(f"{self.bin_number}\t{self.iteration}\t{convergence}\t{output}\n")
