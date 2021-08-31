<h1 align="center">AmpPy - A Python Wrapper for AmpTools</h1>


## Requirements
* [AmpTools](https://github.com/mashephe/AmpTools/tree/master/AmpTools) (obviously)
* [Hall D Simulation Software](https://github.com/JeffersonLab/halld_sim) (for "fit" and "split_mass" scripts and "Zlm" amplitude)

## Install
Download a wheel binary for Linux at the [releases page](https://github.com/denehoffman/amppy/releases)
```shell
$ pip3 install amppy-0.0.1-cp36-cp36m-linux_x86_64.whl
```

## Usage
```shell
$ amppy
usage: amppy <command> [<args>]

Possible commands include:
    generate    Generate an AmpTools configuration file
    divide      Divide data into bins in a new fit directory
    add         Add a configuration file to an existing fit directory
    fit         Run fits using AmpTools
    bootstrap   Bootstrap existing fits using AmpTools
    plot        Plot results

See 'amppy <command> --help' to read about a specific subcommand
```
### Typical workflow:
```shell
$ amppy generate # create a new config file, call it "etapi_D_waves.cfg" for example
$ amppy divide -o PWA_DIR --low 1.0 --high 1.8 -n 20 -d <path to data> -g <path to thrown MC> -a <path to accepted MC> ~/etapi_D_waves.cfg
$ amppy generate # maybe we want to create a config with some different waves to compare, like "etapi_S+D_waves.cfg"
$ amppy add -o PWA_DIR ~/etapi_S+D_waves.cfg
$ amppy fit Pool PWA_DIR --iterations 20 --processes 15 # amppy will give you a menu to select the config file you want to fit with
$ amppy fit Pool PWA_DIR --iterations 20 --processes 15 # so we can fit both by running it twice and selecting different configs
$ amppy bootstrap Pool PWA_DIR --iterations 20 --processes 15 # changing the command from "fit" to "bootstrap" causes amppy
$ amppy bootstrap Pool PWA_DIR --iterations 20 --processes 15 # to select the best fit, create bootstrapped config files, and run an new fit
$ amppy plot PWA -o "D_waves_only.pdf"
$ amppy plot PWA -o "S_and_D_waves.pdf"
```
Most of the ```amppy``` commands contain menus or command line interfaces which give the commands more functionality than is shown here. For example, the plot command allows the user to select from a number of plot types which include intensity plots and statistical plots to tell the user how well the fits converged.

### From a Python script:
```py
# example.py
from amppy.dividers import Divider_split_mass
from amppy.backends.PythonMultiprocessing import PythonMultiprocessing
from amppy.plotting.Plotter_Intensity import Plotter_Intensity
import matplotlib.backends.backend_pdf as backend_pdf

div = Divider_split_mass()
div.divide(low=1.0, high=1.8 # mass range in GeV
           nbins=20, # 20 bins
           root="~/my_pwa", # output directory
           config="~/etapi_D_waves.cfg", # AmpTools config
           data="~/data/", gen="~/thrownMC/", acc="~/acceptedMC/", bkg=None) # locations of ROOT flat trees for AmpTools
disp = PythonMultiprocessing()
disp.setup(root="~/my_pwa", config="~/etapi_D_waves.cfg",
           iterations=100, # run 100 iterations for each bin (2000 fits total)
           seed=1927428, # set a seed
           bootstrap=False, # can't bootstrap on the first fit
           verbosity=1) # verbosity (show standard loading bar)
disp.dispatch(processes=15)
plotter = Plotter_Intensity(config="~/etapi_D_waves.cfg",
                            pdf=None) # optionally, you can supply a path
plotter.plot({"acceptance_corrected": True,
              "xlabel_invmass": f"m($\eta\pi_0$) GeV/$c^2$"})
print(f"Output saved to {str(plotter.pdf_path)}")
```
```shell
$ python3 example.py
...
Output saved to ~/my_pwa/eta_pi_D_waves_plots.pdf
```

## TODO
* Add the following plotting methods:
    * a display of the complex amplitudes in a 2D scatter plot for each wave in each bin
    * add confidence intervals for bootstrapping
    * plot angular distributions for each bin and the fit projections onto the accepted MC
* Create a divider for ```split_t```
* Write a generator for SDME config files
* Write a plotting method for SDMEs
* Write API documentation
