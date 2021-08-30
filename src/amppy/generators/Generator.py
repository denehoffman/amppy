from abc import ABC, abstractmethod
from pathlib import Path
from colorama import Fore, Style, init
init()

class Generator(ABC):

    @abstractmethod
    def write_constants(self):
        pass

    @abstractmethod
    def write_parameters(self):
        pass

    @abstractmethod
    def write_loops(self):
        pass

    @abstractmethod
    def write_paths(self):
        pass

    @abstractmethod
    def write_sums(self):
        pass

    @abstractmethod
    def write_amplitudes(self):
        pass

    @abstractmethod
    def write_initialization(self):
        pass

    @abstractmethod
    def write_constraints(self):
        pass

    @abstractmethod
    def write_scales(self):
        pass

    @abstractmethod
    def write_other(self):
        pass

    def preview(self):
        print(Style.BRIGHT)
        print(Fore.BLUE)
        print(self.write_other())
        print(Fore.GREEN)
        print(self.write_constants())
        print(self.write_parameters())
        print(Fore.YELLOW)
        print(self.write_loops())
        print(self.write_paths())
        print(self.write_sums())
        print(Fore.MAGENTA)
        print(self.write_amplitudes())
        print(Fore.CYAN)
        print(self.write_initialization())
        print(self.write_constraints())
        print(self.write_scales())
        print(Style.RESET_ALL)
        input("Press <enter> to continue")


    def write_all(self):
        file_exists = True
        while file_exists:
            filename = input("Enter a name for the new config file: ")
            if not filename.endswith(".cfg"):
                filename += ".cfg"
            file_path = Path(filename).resolve()
            if file_path.is_file():
                print("Please select a different name, that one is already taken!")
            else:
                file_exists = False
        with open(file_path, 'w') as f:
            f.write(self.write_other().replace("@filename", file_path.stem) + '\n')
            f.write(self.write_constants() + '\n')
            f.write(self.write_parameters() + '\n')
            f.write(self.write_loops() + '\n')
            f.write(self.write_paths() + '\n')
            f.write(self.write_sums() + '\n')
            f.write(self.write_amplitudes() + '\n')
            f.write(self.write_initialization() + '\n')
            f.write(self.write_constraints() + '\n')
            f.write(self.write_scales() + '\n')

    @abstractmethod
    def show_menu(self):
        pass
