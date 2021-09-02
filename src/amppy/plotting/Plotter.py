from abc import ABC, abstractmethod
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
import numpy as np
from halo import Halo

class Plotter(ABC):
    pdf = None
    pdf_path = None

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
        ### Fit DataFrame
        self.fit_df = pd.read_csv(self.fit_results, delimiter='\t', index_col=False)
        amp_typing = {col: 'complex' for col in self.fit_df.columns if "AMP" in col}
        self.fit_df = self.fit_df.astype(amp_typing)
        amp_agg = {col: [np.real, np.imag] for col in amp_typing}
        amp_names = [col + tag for col in amp_typing for tag in ["_re", "_im"]]
        self.fit_df[amp_names] = self.fit_df.agg(amp_agg)
        self.fit_df['nlikelihood'] = self.fit_df['likelihood'].to_numpy() / self.fit_df['total_AC_INT'].to_numpy()
        ### Best Fit DataFrame
        self.best_fit_df = self.fit_df.loc[self.fit_df.groupby(['Bin'])['likelihood'].idxmax()]
        ### Bin Info DataFrame (columns = "bin=#,#" and "mass"/"t" etc)
        self.bin_info_df = pd.read_csv(self.bin_info, delimiter='\t')
        self.bin_type = self.bin_info_df.columns.to_list()[1] # e.g. "mass=GeV/$c^2$"
        self.bin_unit = self.bin_type.split("=")[1] # e.g. "GeV/$c^2$"
        bin_edge_low, bin_edge_high = [float(val) for val in self.bin_info_df.columns.to_list()[0].split('=')[1].split(',')]
        self.nbins = len(self.bin_info_df) # number of bins
        self.bin_centers = self.bin_info_df[self.bin_type].to_list() # values of bin centers
        self.fit_df['Center'] = self.bin_info_df[self.bin_type].iloc[self.fit_df['Bin']].to_list()
        self.best_fit_df['Center'] = self.bin_info_df[self.bin_type].iloc[self.best_fit_df['Bin']].to_list()
        self.bin_info_df['Fit'] = [bin_n in self.best_fit_df['Bin'] for bin_n in range(self.nbins)] # bool array, true if a fit converged
        self.bin_width = (bin_edge_high - bin_edge_low) / self.nbins # bin width
        self.bin_edges = [bin_edge_low + n * self.bin_width for n in range(self.nbins + 1)] # bin edges (len = nbins+1)
        self.bin_info_df['Label'] = [f"({round(low_edge, 3)} - {round(high_edge, 3)}) {self.bin_unit}" for low_edge, high_edge in zip(self.bin_edges[:-1], self.bin_edges[1:])]
        ### list whose n-th element is a DataFrame with all converged fits in the n-th bin
        self.fits_in_bin = [self.fit_df.loc[self.fit_df['Bin'] == bin_num] for bin_num in range(self.nbins)]
        self.bootstrap_df = None
        self.bootstrapped = False
        if self.bootstrap.exists():
            self.bootstrap_df = pd.read_csv(self.bootstrap, delimiter='\t', index_col=False)
            amp_typing = {col: 'complex' for col in self.bootstrap_df.columns if "AMP" in col}
            self.bootstrap_df = self.bootstrap_df.astype(amp_typing)
            amp_agg = {col: [np.real, np.imag] for col in amp_typing}
            amp_names = [col + tag for col in amp_typing for tag in ["_re", "_im"]]
            self.bootstrap_df[amp_names] = self.bootstrap_df.agg(amp_agg)
            self.bootstrap_df['Center'] = self.bin_info_df[self.bin_type].iloc[self.bootstrap_df['Bin']].to_list()
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
            if Plotter.pdf is None:
                self.pdf_path = Path(config).resolve().parent / (Path(config).resolve().stem + "_plots.pdf")
                self.pdf = matplotlib.backends.backend_pdf.PdfPages(str(self.pdf_path))
                Plotter.pdf = self.pdf
                Plotter.pdf_path = self.pdf_path
            else:
                self.pdf_path = Plotter.pdf_path
                self.pdf = Plotter.pdf
        else:
            if Plotter.pdf is None:
                if not pdf.endswith(".pdf"):
                    pdf += ".pdf"
                self.pdf_path = Path(pdf).resolve()
                self.pdf = matplotlib.backends.backend_pdf.PdfPages(str(self.pdf_path))
                Plotter.pdf = self.pdf
                Plotter.pdf_path = self.pdf_path
            else:
                self.pdf_path = Plotter.pdf_path
                self.pdf = Plotter.pdf
    
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
