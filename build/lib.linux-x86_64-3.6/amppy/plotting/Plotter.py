from abc import ABC, abstractmethod
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
from halo import Halo

class Plotter(ABC):

    def __init__(self, config, pdf=None):
        self.xlabel = ""
        self.ylabel = "" 
        self.title = ""
        self.config_template = Path(config).resolve()
        self.fit_results = self.config_template.parent / (self.config_template.stem + "::fit_results.txt")
        self.bin_info = self.config_template.parent / 'bin_info.txt'
        self.bootstrap = self.config_template.parent / (self.config_template.stem + "_bootstrap::fit_results.txt")
        self.fit_df = None
        self.best_fit_df = None
        self.fit_df = pd.read_csv(self.fit_results, delimiter='\t', index_col=False)
        self.best_fit_df = self.fit_df.loc[self.fit_df.groupby(['Bin'])['likelihood'].idxmax()]
        self.bin_info_df = pd.read_csv(self.bin_info, delimiter='\t')
        self.bin_type = self.bin_info_df.columns.to_list()[1]
        self.bin_width = self.bin_info_df[self.bin_type].iloc[1] - self.bin_info_df[self.bin_type].iloc[0]
        self.bin_info_df['Centers'] = np.linspace(self.bin_info_df[self.bin_type].iloc[0] + self.bin_width / 2,
                                                  self.bin_info_df[self.bin_type].iloc[-1] - self.bin_width / 2,
                                                  len(self.bin_info_df))
        self.bootstrap_df = None
        self.bootstrapped = False
        if self.bootstrap.exists():
            self.bootstrap_df = pd.read_csv(self.bootstrap, delimiter='\t', index_col=False)
            self.bootstrapped = True
        wave_letters = ['S', 'P', 'D', 'F', 'G']
        amp_score = lambda wave: 100 * wave_letters.index(wave[0]) + (-10 if wave[-2] == '-' else 10) * int(wave[1]) + (-1 if wave[-1] == '-' else 1)
        wave_score = lambda wave: 10 * wave_letters.index(wave[0]) + (-1 if wave[-1] == '-' else 1) * int(wave[1])
        # sneaky way of sorting
        self.amplitudes = sorted(list(set([column.split("_")[0]
                                           for column
                                           in self.fit_df.columns.to_list()
                                           if "AMP" in column])),
                                 key=amp_score)
        self.waves = sorted(list(set([column.split("_")[0][:-1]
                                      for column
                                      in self.fit_df.columns.to_list()
                                      if "AMP" in column])),
                            key = wave_score)
        self.phases = ["_".join(column.split("_")[:2])
                       for column in self.fit_df.columns.to_list()
                       if "_PHASE" in column]
        self.pos_amplitudes = [amp for amp in self.amplitudes if amp.endswith('+')]
        self.neg_amplitudes = [amp for amp in self.amplitudes if amp.endswith('-')]
        self.spinner = Halo(text='Plotting', spinner='dots')
        if pdf is None:
            self.pdf_path = Path(config).resolve().parent / (Path(config).resolve().stem + "_plots.pdf")
            self.pdf = matplotlib.backends.backend_pdf.PdfPages(str(pdf_path))
        else:
            if not pdf.endswith(".pdf"):
                pdf += ".pdf"
            self.pdf_path = Path(pdf).resolve()
            self.pdf = matplotlib.backends.backend_pdf.PdfPages(str(pdf_path))
    
    @staticmethod
    def get_label_from_amplitude(amp_string, refl=False):
        amp_l = amp_string[0]
        amp_m = amp_string[1]
        if int(amp_m) > 0:
            amp_m_sign = amp_string[2]
        else:
            amp_m_sign = ""
        refl_sign = amp_string[-1]
        if refl:
            return f"${amp_l}_{{{amp_m_sign}{amp_m}}}^{{{refl_sign}}}$"
        else:
            return f"${amp_l}_{{{amp_m_sign}{amp_m}}}$"
    
    @staticmethod
    @abstractmethod
    def plotter_description():
        pass

    @staticmethod
    @abstractmethod
    def configure(kwdict):
        pass

    @abstractmethod
    def plot(self, kwdict):
        pass
