import os
import sys
from pathlib import Path
import numpy as np
from simple_term_menu import TerminalMenu
from amppy.generators.Generator import Generator

def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

class Zlm:
    sign = lambda x: x and (+1, -1)[x < 0]
    sign_str = lambda x: {-1: "-", +1: "+", 0: " "}.get(Zlm.sign(x))
    letter = lambda x: ["S", "P", "D", "F", "G"][x]

    def __init__(self, l, m, refl):
        self.reaction = None
        self.l = int(l)
        self.m = int(m)
        self.refl = int(refl)

    def __str__(self):
        m_sign = Zlm.sign_str(self.m)
        refl_sign = Zlm.sign_str(self.refl)
        # 34 characters long
        return f"{Zlm.letter(self.l)}-Wave    L = {self.l}    M = {m_sign}{abs(self.m)}    ε = {refl_sign}"

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        if self.l == other.l:
            if self.m == other.m:
                return (self.refl) > (other.refl)
            return self.m < other.m
        return self.l < other.l

    def __eq__(self, other):
        return (self.l == other.l) and (self.m == other.m) and (self.refl == other.refl)

    def wave_str(self, part='Re', pol=''):
        line = self.reaction + pol + '::'
        line += ('Positive' if self.refl > 0 else 'Negative')
        line += f"{part}::"
        line += Zlm.letter(self.l)
        line += str(abs(self.m))
        if self.l != 0:
            Zlm.sign_str(self.m)
        line += Zlm.sign_str(self.refl)
        return line 
    

class Generator_Zlm(Generator):
    get_pol = lambda x: {'PARA 0': '_000', 'PERP 45': '_045', 'PERP 90': '_090', 'PARA 135': '_135', 'AMO': '_AMO'}.get(x)
    get_pol_val = lambda x: {'PARA 0': '0.3519', 'PERP 45': '0.3374', 'PERP 90': '0.3303', 'PARA 135': '0.3375', 'AMO': '0.00001'}.get(x)
    get_pol_angle = lambda x: {'PARA 0': '0.0', 'PERP 45': '45.0', 'PERP 90': '90.0', 'PARA 135': '135.0', 'AMO': '0.0'}.get(x)
    get_pol_num = lambda x: {'PARA 0': '  0', 'PERP 45': ' 45', 'PERP 90': ' 90', 'PARA 135': '135', 'AMO': 'AMO'}.get(x)

    def __init__(self):
        self.menu_style = {"menu_cursor": "> ",
                           "menu_cursor_style": ("fg_red", "bold"),
                           "menu_highlight_style": ("bg_black", "fg_green")} 
        self.amplitudes = set()
        self.polarizations = ['PARA 0', 'PERP 45', 'PERP 90', 'PARA 135', 'AMO']
        self.reaction = 'default'
        self.file_types = ['DATA', 'ACC', 'GEN', 'NIFILE']
        self.coordinates = 'polar'
        self.particles = ['gamma', 'proton', 'p1', 'p2']

    def write_constants(self):
        lines = ['\n# Constants']
        for pol in self.polarizations:
            lines.append(f"define polVal{Generator_Zlm.get_pol(pol)} {Generator_Zlm.get_pol_val(pol)}")
        lines.append('')
        for pol in self.polarizations:
            lines.append(f"define polAngle{Generator_Zlm.get_pol(pol)} {Generator_Zlm.get_pol_angle(pol)}")
        return '\n'.join(lines)


    def write_parameters(self):
        lines = ['\n# Parameters']
        if len(self.polarizations) > 1:
            lines.append(f"parameter polScale{Generator_Zlm.get_pol(self.polarizations[0])} 1.0 fixed")
            for pol in self.polarizations[1:]:
                lines.append(f"parameter polScale{Generator_Zlm.get_pol(pol)} 1.0")
        return '\n'.join(lines)

    def write_loops(self):
        lines = ['\n# Loops']
        reaction_loop = ['loop', self.reaction]
        for pol in self.polarizations:
            reaction_loop.append(f"{self.reaction}{Generator_Zlm.get_pol(pol)}")
        lines.append(' '.join(reaction_loop))
        lines.append('')
        for file_type in self.file_types:
            file_loop = ['loop', f"LOOP{file_type}"]
            for pol in self.polarizations:
                file_loop.append(f"@{file_type}{Generator_Zlm.get_pol(pol)}")
            lines.append(' '.join(file_loop))
        lines.append('')
        polang_loop = ['loop', 'LOOPPOLANG']
        for pol in self.polarizations:
            polang_loop.append(f"polAngle{Generator_Zlm.get_pol(pol)}")
        lines.append(' '.join(polang_loop))
        polval_loop = ['loop', 'LOOPPOLVAL']
        for pol in self.polarizations:
            polval_loop.append(f"polVal{Generator_Zlm.get_pol(pol)}")
        lines.append(' '.join(polval_loop))
        polscale_loop = ['loop', 'LOOPSCALE']
        if len(self.polarizations) > 1:
            for pol in self.polarizations:
                polscale_loop.append(f"[polScale{Generator_Zlm.get_pol(pol)}]")
            lines.append(' '.join(polscale_loop))
        return '\n'.join(lines)

    def write_paths(self):
        lines = ['\n# Paths']
        lines.append(f"normintfile {self.reaction} LOOPNIFILE")
        lines.append(f"data {self.reaction} LOOPDATA")
        lines.append(f"genmc {self.reaction} LOOPGEN")
        lines.append(f"accmc {self.reaction} LOOPACC")
        if 'BKG' in self.file_types:
            lines.append(f"bkgnd {self.reaction} LOOPBKG")
        return '\n'.join(lines)


    def write_sums(self):
        reflectivities = np.array([amp.refl for amp in self.amplitudes])
        lines = ['\n# Sums']
        if np.any(reflectivities > 0):
            lines.append(f"sum {self.reaction} PositiveRe")
            lines.append(f"sum {self.reaction} PositiveIm")
        if np.any(reflectivities < 0):
            lines.append(f"sum {self.reaction} NegativeRe")
            lines.append(f"sum {self.reaction} NegativeIm")
        return '\n'.join(lines)


    def write_amplitudes(self):
        lines = ['\n# Amplitudes']
        for amp in sorted(list(self.amplitudes)):
            line = f"amplitude {amp.wave_str(part='Re')} Zlm {amp.l} {amp.m} "
            line += '+1 '
            line += '+1 ' if amp.refl > 0 else '-1 '
            line += "LOOPPOLANG LOOPPOLVAL"
            lines.append(line)
            line = f"amplitude {amp.wave_str(part='Im')} Zlm {amp.l} {amp.m} "
            line += '-1 '
            line += '-1 ' if amp.refl > 0 else '+1 '
            line += "LOOPPOLANG LOOPPOLVAL"
            lines.append(line)
        return '\n'.join(lines)


    def write_initialization(self):
        reflectivities = np.array([amp.refl for amp in self.amplitudes])
        lines = ['\n# Initialize Amplitudes']
        amp_list = sorted(list(self.amplitudes))
        need_pos_real = np.any(reflectivities > 0)
        need_neg_real = np.any(reflectivities < 0)
        for amp in sorted(list(self.amplitudes)):
            if amp.refl > 0:
                if need_pos_real:
                    line = f"initialize {amp.wave_str(part='Re')} {self.coordinates} @uniform 0.0 real"
                    need_pos_real = False
                else:
                    line = f"initialize {amp.wave_str(part='Re')} {self.coordinates} @uniform @uniform"
            else:
                if need_neg_real:
                    line = f"initialize {amp.wave_str(part='Re')} {self.coordinates} @uniform 0.0 real"
                    need_neg_real = False
                else:
                    line = f"initialize {amp.wave_str(part='Re')} {self.coordinates} @uniform @uniform"
            lines.append(line)
        return '\n'.join(lines)

                
    def write_constraints(self):
        lines = ['\n# Constrain Amplitudes']
        for amp in sorted(list(self.amplitudes)):
            lines.append(f"constrain {amp.wave_str(part='Re')} {amp.wave_str(part='Im')}")
            lines.append(f"constrain {amp.wave_str(part='Re', pol=Generator_Zlm.get_pol(self.polarizations[0]))} {amp.wave_str(part='Re')}")
        return '\n'.join(lines)

    def write_scales(self):
        lines = ['\n# Scale Amplitudes']
        if len(self.polarizations) > 1:
            for amp in sorted(list(self.amplitudes)):
                lines.append(f"scale {amp.wave_str(part='Re')} LOOPSCALE")
        return '\n'.join(lines)

    def write_other(self):
        lines = ['##########################################################',
                 '# This is an AmpTools configuration written by AmpPy     #',
                 '# Modify the content with caution--AmpPy uses @tags      #',
                 '# to replace placeholder content like file paths, seeds, #',
                 '# and initializations                                    #',
                 '##########################################################\n']
        lines.append("fit @filename")
        lines.append(f"reaction {self.reaction} {' '.join(self.particles)}")
        return '\n'.join(lines)


    def print_header(self):
        wave_len = 50
        top = "╔═" + "═" * wave_len + "═╗"
        mid = "╠═" + "═" * wave_len + "═╣"
        bot = "╚═" + "═" * wave_len + "═╝"
        redge ="║ " 
        ledge =" ║" 
        print(top)
        reaction_content = f"Reaction Name: {self.reaction}"
        print(redge + reaction_content + " " * (wave_len - len(reaction_content)) + ledge)
        print(mid)
        wave_list = sorted(list(self.amplitudes))
        s_waves = "\n".join(
            [redge + str(wave) + " " * (wave_len - len(str(wave))) + ledge for wave in wave_list if wave.l == 0])
        p_waves = "\n".join(
            [redge + str(wave) + " " * (wave_len - len(str(wave))) + ledge for wave in wave_list if wave.l == 1])
        d_waves = "\n".join(
            [redge + str(wave) + " " * (wave_len - len(str(wave))) + ledge for wave in wave_list if wave.l == 2])
        if len(s_waves):
            print(s_waves)
            print(mid)
        if len(p_waves):
            print(p_waves)
            print(mid)
        if len(d_waves):
            print(d_waves)
            print(mid)
        pol_string = " ".join([Generator_Zlm.get_pol_num(pol) for pol in self.polarizations])
        pol_content = "Polarizations " + pol_string
        print(redge + pol_content + " " * (wave_len - len(pol_content)) + ledge)
        coordinate_content = "Coordinate System: " + ('polar' if self.coordinates == 'polar' else 'cartesian')
        print(redge + coordinate_content + " " * (wave_len - len(coordinate_content)) + ledge)
        background_content = "Use Background ROOT Files: " + ('yes' if 'BKG' in self.file_types else 'no')
        print(redge + background_content + " " * (wave_len - len(background_content)) + ledge)
        particles_content = f"Particle Names: {' '.join(self.particles)}"
        print(redge + particles_content + " " * (wave_len - len(particles_content)) + ledge)
        print(bot)
        print()

    def show_menu(self):
        while True:
            self.main_menu()

    def main_menu(self):
        title = "AmpTools Zlm Configuration Generator"
        items = ["Add Waves",
                 "Remove Waves",
                 "Edit Reaction Name",
                 "Edit Polarizations",
                 "Toggle Coordinate System",
                 "Toggle Background",
                 "Edit Particle Names",
                 "Preview",
                 "Generate",
                 "Exit"]
        menu = TerminalMenu(menu_entries=items,
                            title=title,
                            **self.menu_style)
        clear()
        self.print_header()
        sel = menu.show()
        if items[sel] == "Add Waves":
            self.add_menu()
        elif items[sel] == "Remove Waves":
            if self.amplitudes:
                self.remove_menu()
        elif items[sel] == "Edit Reaction Name":
            clear()
            print("Enter a new reaction name or leave blank for 'default'")
            name = input("> ").replace(" ", "")
            if len(name):
                self.reaction = name
            else:
                self.reaction = 'default'
            for amp in self.amplitudes:
                amp.reaction = self.reaction
        elif items[sel] == "Edit Polarizations":
            self.pol_menu()
        elif items[sel] == "Toggle Coordinate System":
            if self.coordinates == 'polar':
                self.coordinates = 'cartesian'
            else:
                self.coordinates = 'polar'
        elif items[sel] == "Toggle Background":
            if 'BKG' in self.file_types:
                self.file_types.remove('BKG')
            else:
                self.file_types.append('BKG')
        elif items[sel] == "Edit Particle Names":
            clear()
            print("Enter particle names separated by a space")
            print("Leave blank to use the default names: gamma proton p1 p2")
            name_string = input("> ")
            if len(name_string):
                self.particles = name_string.strip().split(" ")
            else:
                self.particles = ['gamma', 'proton', 'p1', 'p2']
        elif items[sel] == "Preview":
            clear()
            self.preview()
        elif items[sel] == "Generate":
            self.write_all()
        else:
            sys.exit(1)


    def add_menu(self):
        title = "Add Waves\n"
        items = ["S Wave", "P Wave", "D Wave"]
        menu = TerminalMenu(menu_entries=items,
                            title=title,
                            cycle_cursor=True,
                            clear_screen=True,
                            **self.menu_style)
        l = menu.show()
        m = self.m_menu(l) 
        r_selected = False
        while not r_selected:
            refls = self.r_menu()
            if not refls:
                print("You must select at least one reflectivity!")
            else:
                r_selected = True
                for refl in refls:
                    amp = Zlm(l, m, refl)
                    amp.reaction = self.reaction
                    self.amplitudes.add(amp)


    def m_menu(self, l):
        if l > 0:
            title = f"Select {Zlm.letter(l)} Orbital M\n"
            items = list(map(str, reversed(range(-(l + 1) + 1, l + 1))))
            menu = TerminalMenu(menu_entries=items,
                                title=title,
                                cycle_cursor=True,
                                clear_screen=True,
                                **self.menu_style)
            sel = menu.show()
            return items[sel]
        else:
            return 0

    def r_menu(self):
        title = "Select Reflectivity\n"
        items = ["+1", "-1"]
        menu = TerminalMenu(menu_entries=items,
                            title=title,
                            cycle_cursor=True,
                            clear_screen=True,
                            multi_select=True,
                            show_multi_select_hint=True,
                            **self.menu_style)
        sels = menu.show()
        items = np.array(items)
        return items[list(sels)].tolist()

    def pol_menu(self):
        title = "Select Polarizations\n"
        items = ['PARA 0', 'PERP 45', 'PERP 90', 'PARA 135', 'AMO']
        menu = TerminalMenu(menu_entries=items,
                            title=title,
                            cycle_cursor=True,
                            clear_screen=True,
                            multi_select=True,
                            show_multi_select_hint=True,
                            **self.menu_style)
        sels = menu.show()
        items = np.array(items)
        self.polarizations = items[list(sels)].tolist()


    def remove_menu(self):
        wave_list = sorted(list(self.amplitudes))
        wave_list.append("Cancel")
        title = "Remove Waves\n"
        items = [str(wave) for wave in wave_list]
        menu = TerminalMenu(menu_entries=items,
                            title=title,
                            cycle_cursor=True,
                            clear_screen=True,
                            multi_select=True,
                            show_multi_select_hint=True,
                            **self.menu_style)
        sels = menu.show()
        if items[sels[-1]] != "Cancel":
            for sel in sels:
                self.amplitudes.remove(wave_list[sel])
