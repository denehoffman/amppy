#!python
import sys
from amppy.backends.Fitter import Fitter
from pathlib import Path

if __name__ == "__main__":
    f = Fitter()
    f.setup(Path(str(sys.argv[1])), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), str(sys.argv[5]), str(sys.argv[6]) == "True", Path(str(sys.argv[7])))
    # setup(self, bin_directory: Path, bin_number: int, iteration: int, seed: int, reaction: str, bootstrap: bool, config_template: Path)
    f.fit()
