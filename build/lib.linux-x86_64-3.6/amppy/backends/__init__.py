from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from amppy.backends.Dispatcher import Dispatcher

package_dir = Path(__file__).resolve().parent
dispatchers = []
dispatcher_descriptions = []
for (_, module_name, _) in iter_modules([package_dir]):
    module = import_module(f"{__name__}.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if isclass(attribute):
            if issubclass(attribute, Dispatcher):
                if attribute != Dispatcher:
                    # get list of valid dispatcher classes
                    dispatchers.append(attribute)
                    dispatcher_descriptions.append(attribute.dispatcher_description())
