from amppy.plotting.Plotter import Plotter
import argparse
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from halo import Halo
import numpy as np

class Plotter_Bootstrap(Plotter):

    @staticmethod
    def plotter_description():
        return ("Plot Bootstrapped Intensities", "Plots intensities with bootstrapped error bars") 
    
    @staticmethod
    def configure(kwdict):
        if not "acceptance_corrected" in kwdict:
            kwdict["acceptance_corrected"] = input("Use acceptance corrected values? (y/n)\n> ") == 'y'
        if not "xlabel_invmass" in kwdict:
            particles = input("Input the x-axis label to be used for the invariant mass (example: 'K_SK_S' for two K-short particles)\n> ")
            kwdict["xlabel_invmass"] = f"m$({particles})$ GeV/$c^2$"
        return kwdict

    def plot_wave(self, wave, tag, err_tag):
        fig = plt.figure()
        if wave + "+" in self.amplitudes:
            amp = wave + "+"
            plt.errorbar(self.best_fit_df['Center'],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color='r',
                            label=f"$+\epsilon$")
        if wave + "-" in self.amplitudes:
            amp = wave + "-"
            plt.errorbar(self.best_fit_df['Center'],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color='k',
                            label=f"$-\epsilon$")
        plt.errorbar(self.best_fit_df['Center'],
                        self.best_fit_df['total' + tag],
                        yerr=self.best_fit_df['total' + err_tag],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
        plt.hist(self.best_fit_df['Center'],
                    bins=len(self.bin_info_df),
                    range=(self.bin_edges[0], self.bin_edges[-1]),
                    weights=self.best_fit_df['total' + tag],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
        plt.title(Plotter.get_label_from_amplitude(amp) + " (Bootstrapped)")
        plt.ylim(bottom=0)
        span = self.bin_edges[-1] - self.bin_edges[0]
        buf = span * 0.13
        plt.xlim(self.bin_edges[0] - buf, self.bin_edges[-1] + buf)
        plt.ylabel("Intensity")
        plt.xlabel(self.xlabel)
        plt.legend()
        plt.tight_layout()
        self.pdf.savefig(fig, dpi=300)
        plt.close()

    def plot_amps(self, amps, title, tag, err_tag):
        fig = plt.figure()
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown", "tab:pink", "tab:olive", "tab:cyan"]
        for i, amp in enumerate(amps):
            plt.errorbar(self.best_fit_df['Center'],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color=colors[i],
                            label=Plotter.get_label_from_amplitude(amp, refl=True))
        plt.errorbar(self.best_fit_df['Center'],
                        self.best_fit_df['total' + tag],
                        yerr=self.best_fit_df['total' + err_tag],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
        plt.hist(self.best_fit_df['Center'],
                    bins=len(self.bin_info_df),
                    range=(self.bin_edges[0], self.bin_edges[-1]),
                    weights=self.best_fit_df['total' + tag],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
        plt.title(title + " (Bootstrapped)")
        plt.ylim(bottom=0)
        span = self.bin_edges[-1] - self.bin_edges[0]
        buf = span * 0.13
        plt.xlim(self.bin_edges[0] - buf, self.bin_edges[-1] + buf)
        plt.ylabel("Intensity")
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
        self.spinner.start("Locating bootstrapped fit")
        if not self.bootstrapped:
            self.spinner.fail("Bootstrapped fit not found, this plot will not be added!")
            return
        else:
            self.spinner.succeed("Bootstrap fit found!")
        self.spinner.start("Calculating bootstrapped parameters and uncertainties")
        for amp in self.amplitudes + ["total"]:
            amp_bootstrap_error = []
            amp_bootstrap_value = []
            for bin_n in range(len(self.bin_info_df)):
                bootstrap_bin_df = self.bootstrap_df.loc[self.bootstrap_df['Bin'] == bin_n]
                amp_bootstrap_error.append(bootstrap_bin_df.loc[:, amp + tag].std())
                amp_bootstrap_value.append(bootstrap_bin_df.loc[:, amp + tag].mean())
            self.best_fit_df.loc[:, amp + err_tag + "_bootstrap"] = amp_bootstrap_error
            self.best_fit_df.loc[:, amp + tag + "_bootstrap"] = amp_bootstrap_value
        self.spinner.succeed("Calculated bootstrapped parameters and uncertainties!")
        self.spinner.start("Plotting individual amplitudes")
        for wave in self.waves:
            self.plot_wave(wave, tag + "_bootstrap", err_tag + "_bootstrap")
        self.spinner.succeed()
        if self.pos_amplitudes:
            self.spinner.start("Plotting all amplitudes with positive reflectivity together")
            self.plot_amps(self.pos_amplitudes, "Positive Reflectivity", tag + "_bootstrap", err_tag + "_bootstrap")
            self.spinner.succeed()
        if self.neg_amplitudes:
            self.spinner.start("Plotting all amplitudes with negative reflectivity together")
            self.plot_amps(self.neg_amplitudes, "Negative Reflectivity", tag + "_bootstrap", err_tag + "_bootstrap")
            self.spinner.succeed()
        self.spinner.start("Plotting all amplitudes together")
        fig = plt.figure()
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown", "tab:pink", "tab:olive", "tab:cyan"]
        for i, amp in enumerate(self.pos_amplitudes):
            plt.errorbar(self.best_fit_df['Center'],
                            self.best_fit_df[amp + tag + "_bootstrap"],
                            yerr=self.best_fit_df[amp + err_tag + "_bootstrap"],
                            elinewidth=0.5,
                            fmt='o',
                            color=colors[i],
                            label=Plotter.get_label_from_amplitude(amp, refl=True))
        for i, amp in enumerate(self.neg_amplitudes):
            plt.errorbar(self.best_fit_df['Center'],
                            self.best_fit_df[amp + tag + "_bootstrap"],
                            yerr=self.best_fit_df[amp + err_tag + "_bootstrap"],
                            elinewidth=0.5,
                            fmt='s',
                            color=colors[i],
                            label=Plotter.get_label_from_amplitude(amp, refl=True))
        plt.errorbar(self.best_fit_df['Center'],
                        self.best_fit_df['total' + tag + "_bootstrap"],
                        yerr=self.best_fit_df['total' + err_tag + "_bootstrap"],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
        plt.hist(self.best_fit_df['Center'],
                    bins=len(self.bin_info_df),
                    range=(self.bin_edges[0], self.bin_edges[-1]),
                    weights=self.best_fit_df['total' + tag + "_bootstrap"],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
        plt.title("All Amplitudes (Bootstrapped)")
        plt.ylim(bottom=0)
        span = self.bin_edges[-1] - self.bin_edges[0]
        buf = span * 0.13
        plt.xlim(self.bin_edges[0] - buf, self.bin_edges[-1] + buf)
        plt.ylabel("Intensity")
        plt.xlabel(self.xlabel)
        plt.legend()
        plt.tight_layout()
        self.pdf.savefig(fig, dpi=300)
        plt.close()
        self.spinner.succeed("Finished plotting intensities!")
