from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from amppy.plotting.Plotter import Plotter

package_dir = Path(__file__).resolve().parent
plotters = []
plotter_descriptions = []
for (_, module_name, _) in iter_modules([package_dir]):
    module = import_module(f"{__name__}.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if isclass(attribute):
            if issubclass(attribute, Plotter):
                if attribute != Plotter:
                    # get list of valid plotter classes
                    plotters.append(attribute)
                    plotter_descriptions.append(attribute.plotter_description())
