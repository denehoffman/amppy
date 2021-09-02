from amppy.dividers.Divider import Divider
from os import system
from shutil import copy
import argparse

class Divider_split_mass(Divider):
    def gen_config(self):
        root_config_destination = self.root_directory / self.config_template.name
        copy(self.config_template, root_config_destination)
        file_to_tag = {"AMO": "_AMO",
                       "PARA_0": "_000",
                       "PERP_45": "_045",
                       "PERP_90": "_090",
                       "PARA_135": "_135"}
        for i in range(self.n_bins):
            bin_dir = self.bin_dirs[int(i)]
            gen_files = list(bin_dir.glob(f"*_GEN__{int(i)}.root"))
            acc_files = list(bin_dir.glob(f"*_ACCEPT__{int(i)}.root"))
            data_files = list(bin_dir.glob(f"*_DATA__{int(i)}.root"))
            bkg_files = list(bin_dir.glob(f"*_BKG__{int(i)}.root"))
            with open(self.config_template) as config:
                config_text = config.read()
                for file_pol, tag_pol in file_to_tag.items():
                    for f in gen_files:
                        if file_pol in f.name:
                            config_text = config_text.replace("@GENFILE" + tag_pol,
                                                              "../" + f.name)
                    for f in acc_files:
                        if file_pol in f.name:
                            config_text = config_text.replace("@ACCFILE" + tag_pol,
                                                              "../" + f.name)
                    for f in data_files:
                        if file_pol in f.name:
                            config_text = config_text.replace("@DATAFILE" + tag_pol,
                                                              "../" + f.name)
                            config_text = config_text.replace("@NIFILE" + tag_pol,
                                                              self.config_template.stem + "_NIFILE" + tag_pol)
                    for f in bkg_files:
                        if file_pol in f.name:
                            config_text = config_text.replace("@BKGFILE" + tag_pol,
                                                              "../" + f.name)
            bin_config_path = bin_dir / (self.config_template.stem + "_" + str(i) + ".cfg")
            with open(bin_config_path, 'w') as bin_config:
                bin_config.write(config_text)


    def divide_file(self, in_file, out_stem, **kwargs):
        if "DATA" in out_stem:
            tree_name = kwargs.get("data_tree")
        elif "GEN" in out_stem:
            tree_name = kwargs.get("generated_tree")
        elif "ACCEPT" in out_stem:
            tree_name = kwargs.get("accepted_tree")
        elif "BKG" in out_stem:
            tree_name = kwargs.get("background_tree")

        if tree_name == None:
            tree_name = "kin"

        system(f"split_mass {str(in_file)} {str(out_stem)} {' '.join(map(str, self.low_high_tuple))} {str(self.n_bins)} -T {tree_name}:kin")
