from amppy.plotting.Plotter import Plotter
import argparse
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from halo import Halo
import numpy as np

class Plotter_Statistics(Plotter):

    @staticmethod
    def plotter_description():
        return ("Plot Statistics", "Plots violin plots for the fit intensities and likelihood") 
    
    @staticmethod
    def configure(kwdict):
        if not "acceptance_corrected" in kwdict:
            kwdict["acceptance_corrected"] = input("Use acceptance corrected values? (y/n)\n> ") == 'y'
        if not "xlabel_invmass" in kwdict:
            particles = input("Input the x-axis label to be used for the invariant mass (example: 'K_SK_S' for two K-short particles)\n> ")
            kwdict["xlabel_invmass"] = f"m$({particles})$ GeV/$c^2$"
        return kwdict


    def plot_violin(self, amp, tag, title, ylabel):
        fig = plt.figure()
        all_runs_by_bin = [self.fit_df[amp + tag].loc[self.fit_df['Bin'] == bin_num] for bin_num in self.bin_info_df['bin']]
        plt.scatter(self.bin_info_df['Centers'].iloc[self.fit_df['Bin']],
                    self.fit_df[amp + tag],
                    marker='.',
                    color='k',
                    label="Fit Minima")
        plt.violinplot(all_runs_by_bin,
                        self.bin_info_df['Centers'],
                        widths=self.bin_width,
                        showmeans=True,
                        showextrema=True,
                        showmedians=True)
        plt.scatter(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                    self.best_fit_df[amp + tag],
                    marker='o',
                    color='r',
                    label="Selected Minimum")
        plt.title(title)
        if 'likelihood' in amp:
            plt.ylim(top=0)
        else:
            plt.ylim(bottom=0)
        span = self.bin_info_df['Centers'].iloc[-1] - self.bin_info_df['Centers'].iloc[0]
        buf = span * 0.13
        plt.xlim(self.bin_info_df['Centers'].iloc[0] - buf,
                    self.bin_info_df['Centers'].iloc[-1] + buf)
        plt.ylabel(ylabel)
        plt.xlabel(self.xlabel)
        plt.legend()
        plt.tight_layout()
        self.pdf.savefig(fig, dpi=300)
        plt.close()

    def plot(self, kwdict):
        plt.rcParams["figure.figsize"] = (20, 10)
        plt.rcParams["font.size"] = 24
        if kwdict.get("acceptance_corrected"):
            tag = "_AC_INT"
            err_tag = "_AC_INT_err"
        else:
            tag = "_NC_INT"
            err_tag = "_NC_INT_err"
        self.xlabel = kwdict.get("xlabel_invmass")
        self.spinner.start("Generating statistical plots for each amplitude")
        for amp in self.amplitudes:
            self.plot_violin(amp, tag, Plotter.get_label_from_amplitude(amp), "Intensity")
        self.spinner.succeed("Plotted statistics for each amplitude!")
        self.spinner.start("Generating statistical plot for the total intensity")
        self.plot_violin("total", tag, "Total Intensity", "Intensity")
        self.spinner.succeed("Plotted statistics for the total intensity!")
        self.spinner.start("Generating plot of likelihood")
        self.plot_violin("likelihood", "", "Log(Likelihood)", "Log(Likelihood)")
        self.spinner.succeed("Plotted likelihood!")
        self.spinner.start("Generating plot of likelihood normalized by total intensity")
        self.fit_df['nlikelihood'] = self.fit_df['likelihood'].to_numpy() / self.fit_df['total' + tag].to_numpy()
        self.best_fit_df['nlikelihood'] = self.best_fit_df['likelihood'].to_numpy() / self.best_fit_df['total' + tag].to_numpy()
        self.plot_violin("nlikelihood", "", "Log(Likelihood)/Total Intensity", "Log(Likelihood)/Total Intensity")
        self.spinner.succeed("Plotted normalized likelihood!")
