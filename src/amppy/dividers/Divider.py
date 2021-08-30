from abc import ABC, abstractmethod
import errno
from pathlib import Path
import numpy as np
import os
from halo import Halo

class Divider(ABC):


    def __init__(self):
        self._root_directory = None
        self._config_template = None
        self._low_high_tuple = None
        self._n_bins = None
        self._data_directory = None
        self._generated_directory = None
        self._accepted_directory = None
        self._background_directory = None
        self._tmp_directory = None
        self._config_replacements = None
    
    @abstractmethod
    def gen_config(self):
        pass


    @abstractmethod
    def divide_file(self, in_file, out_stem, **kwargs):
        pass


    @property
    def root_directory(self):
        return self._root_directory

    @root_directory.setter
    def root_directory(self, path):
        if path.is_dir():
            print(f"Working Directory: {path}")
            self._root_directory = path
        else:
            path.mkdir(parents=True)
            print(f"Working Directory: {path}")
            self._root_directory = path

    @property
    def config_template(self):
        return self._config_template

    
    @config_template.setter
    def config_template(self, path):
        if path.is_file():
            print(f"AmpTools Config Template: {path}")
            self._config_template = path
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def low_high_tuple(self):
        return self._low_high_tuple

    
    @low_high_tuple.setter
    def low_high_tuple(self, tup):
        low, high = tup
        assert low <= high, "Low value must be smaller than high value"
        self._low_high_tuple = (low, high)

    @property
    def n_bins(self):
        return self._n_bins

    @n_bins.setter
    def n_bins(self, n):
        assert n > 0, "Must have a positive number of bins"
        self._n_bins = n

    @property
    def data_directory(self):
        return self._data_directory

    @data_directory.setter
    def data_directory(self, path):
        if path.is_dir():
            self._data_directory = path
            files = path.glob("*.root")
            print("Data files:")
            print("---")
            for f in files:
                print(f"\t{f.name}")
            print("---")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def generated_directory(self):
        return self._generated_directory


    @generated_directory.setter
    def generated_directory(self, path):
        if path.is_dir():
            self._generated_directory = path
            files = path.glob("*.root")
            print("Generated files:")
            print("---")
            for f in files:
                print(f"\t{f.name}")
            print("---")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def accepted_directory(self):
        return self._accepted_directory

    @accepted_directory.setter
    def accepted_directory(self, path):
        if path.is_dir():
            self._accepted_directory = path
            files = path.glob("*.root")
            print("Accepted files:")
            print("---")
            for f in files:
                print(f"\t{f.name}")
            print("---")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    @property
    def background_directory(self):
        return self._background_directory

    @background_directory.setter
    def background_directory(self, path):
        if path.is_dir():
            self._background_directory = path
            files = path.glob("*.root")
            print("Background files:")
            print("---")
            for f in files:
                print(f"\t{f.name}")
            print("---")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))


    def divide_directory(self, in_directory, tag, **kwargs):
        in_files = in_directory.glob("*.root")
        if self._tmp_directory == None:
            self.create_tmp()
        os.chdir(str(self._tmp_directory))
        for in_file in in_files:
            self.divide_file(in_file, in_file.stem + tag, **kwargs)
        os.chdir(str(self.root_directory))

    def write_bin_info(self, header):
        with open(self.root_directory / "bin_info.txt", 'w') as writer:
            bin_content = np.linspace(*self.low_high_tuple, self.n_bins)
            lines = [header]
            for i, content in enumerate(bin_content):
                lines.append(f"{i}\t{content}\n")
            writer.writelines(lines)

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


    def create_tmp(self):
        self._tmp_directory = self._root_directory / f"tmp_{self._config_template.stem}"
        self._tmp_directory.mkdir(exist_ok=True)

    def remove_tmp(self):
        self._tmp_directory.rmdir()

    @property
    def bin_dirs(self):
        return [self.root_directory / str(n) for n in range(self.n_bins)]


    def create_bins(self):
        for bin_dir in self.bin_dirs:
            bin_dir.mkdir(exist_ok=True)


    def bin_split_files(self):
        for n in range(self.n_bins):
            bin_files = self._tmp_directory.glob(f"*_{n}.root")
            for source in bin_files:
                destination = self.bin_dirs[n] / source.name
                source.replace(destination)
        self.remove_tmp()


    def load_paths(self, root, config, data, gen, acc, bkg=None):
        self.root_directory = Path(root).resolve()
        self.config_template = Path(config).resolve()
        self.data_directory = Path(data).resolve()
        self.generated_directory = Path(gen).resolve()
        self.accepted_directory = Path(acc).resolve()
        if bkg != None:
            self.background_directory = path(bkg).resolve()


    def preprocessing(self, **kwargs):
        pass

    def postprocessing(self, **kwargs):
        pass

    

    def divide(self, low, high, n_bins, root, config, data, gen, acc, bkg, variable_name='mass', **kwargs):
        self.preprocessing(**kwargs)
        self.n_bins = n_bins 
        self.low_high_tuple = (low, high)
        self.load_paths(root, config, data, gen, acc, bkg)
        self.create_bins()
        self.write_bin_info(f"bin\t{variable_name}\n")
        spinner = Halo(text='Dividing Data', spinner='dots')
        spinner.start("Dividing data")
        self.divide_directory(self.data_directory, "_DATA_", **kwargs)
        spinner.succeed("Data divided")
        spinner.start("Dividing thrown/generated MC")
        self.divide_directory(self.generated_directory, "_GEN_", **kwargs)
        spinner.succeed("Thrown MC divided")
        spinner.start("Dividing accepted MC")
        self.divide_directory(self.accepted_directory, "_ACCEPT_", **kwargs)
        spinner.succeed("Accepted MC divided")
        if bkg != None:
            spinner.start("Dividing background")
            self.divide_directory(self.data_directory, "_BKG_", **kwargs)
            spinner.succeed("Background divided")
        spinner.start("Moving ROOT files into bins")
        self.bin_split_files()
        spinner.succeed("ROOT files have been binned")
        self.gen_config()
        self.postprocessing(**kwargs)

    
    def add_config(self, root, config):
        self.root_directory = Path(root).resolve()
        self.config_template = Path(config).resolve()
        bin_numbers, _ = self.get_bin_info()
        self.n_bins = len(bin_numbers)
        self.gen_config()


def get_divider_type_string(root):
    bin_info = (Path(root) / "bin_info.txt").resolve()
    output = ""
    if bin_info.exists():
        with open(bin_info) as reader:
            lines = reader.readlines()
            output = lines[0].strip().split("\t")[1]
    return output
