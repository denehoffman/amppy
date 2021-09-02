from amppy.plotting.Plotter import Plotter
import argparse
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from halo import Halo
import numpy as np

class Plotter_Phase(Plotter):

    @staticmethod
    def plotter_description():
        return ("Plot Phases", "Plots the phases between relevant waves") 
    
    @staticmethod
    def configure(kwdict):
        if not "acceptance_corrected" in kwdict:
            kwdict["acceptance_corrected"] = input("Use acceptance corrected values? (y/n)\n> ") == 'y'
        if not "xlabel_invmass" in kwdict:
            particles = input("Input the x-axis label to be used for the invariant mass (example: 'K_SK_S' for two K-short particles)\n> ")
            kwdict["xlabel_invmass"] = f"m$({particles})$ GeV/$c^2$"
        return kwdict

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
        self.spinner.start("Plotting phase differences")
        for phase in self.phases:
            fig, ax = plt.subplots()
            ax2 = ax.twinx()
            ax2.errorbar(self.best_fit_df['Center'],
                         self.best_fit_df[phase + "_PHASE"],
                         yerr=self.best_fit_df[phase + "_PHASE_err"],
                         elinewidth=0.5,
                         fmt='o',
                         color='m',
                         label="Phase Difference")
            ax.errorbar(self.best_fit_df['Center'],
                        self.best_fit_df['total' + tag],
                        yerr=self.best_fit_df['total' + err_tag],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
            ax.hist(self.best_fit_df['Center'],
                    bins=len(self.bin_info_df),
                    range=(self.bin_edges[0], self.bin_edges[-1]),
                    weights=self.best_fit_df['total' + tag],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
            plt.title(f"Phase Difference {phase}")
            plt.ylim(bottom=0)
            span = self.bin_edges[-1] - self.bin_edges[0]
            buf = span * 0.13
            plt.xlim(self.bin_edges[0] - buf, self.bin_edges[-1] + buf)
            ax.set_ylabel("Intensity")
            ax.set_ylim(bottom=0)
            ax2.set_ylabel("Phase")
            ax2.set_ylim(-2 * np.pi, 2 * np.pi)
            ax.set_xlabel(self.xlabel)
            plt.legend()
            plt.tight_layout()
            self.pdf.savefig(fig, dpi=300)
            plt.close()
        self.spinner.succeed("Finished potting phase differences!")


