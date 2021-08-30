from amppy.plotting.Plotter import Plotter
import argparse
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from halo import Halo

class Plotter_Intensity(Plotter):

    @staticmethod
    def plotter_description():
        return ("Plot Intensity", "Plots the fit intensities of each wave") 
    
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
            plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color='r',
                            label=f"$+\epsilon$")
        if wave + "-" in self.amplitudes:
            amp = wave + "-"
            plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color='k',
                            label=f"$-\epsilon$")
        plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                        self.best_fit_df['total' + tag],
                        yerr=self.best_fit_df['total' + err_tag],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
        plt.hist(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                    bins=len(self.bin_info_df),
                    range=(self.bin_info_df[self.bin_type].iloc[0],
                        self.bin_info_df[self.bin_type].iloc[-1]),
                    weights=self.best_fit_df['total' + tag],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
        plt.title(Plotter.get_label_from_amplitude(amp))
        plt.ylim(bottom=0)
        span = self.bin_info_df['Centers'].iloc[-1] - self.bin_info_df['Centers'].iloc[0]
        buf = span * 0.13
        plt.xlim(self.bin_info_df['Centers'].iloc[0] - buf,
                    self.bin_info_df['Centers'].iloc[-1] + buf)
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
            plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color=colors[i],
                            label=Plotter.get_label_from_amplitude(amp, refl=True))
        plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                        self.best_fit_df['total' + tag],
                        yerr=self.best_fit_df['total' + err_tag],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
        plt.hist(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                    bins=len(self.bin_info_df),
                    range=(self.bin_info_df[self.bin_type].iloc[0],
                        self.bin_info_df[self.bin_type].iloc[-1]),
                    weights=self.best_fit_df['total' + tag],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
        plt.title(title)
        plt.ylim(bottom=0)
        span = self.bin_info_df['Centers'].iloc[-1] - self.bin_info_df['Centers'].iloc[0]
        buf = span * 0.13
        plt.xlim(self.bin_info_df['Centers'].iloc[0] - buf,
                    self.bin_info_df['Centers'].iloc[-1] + buf)
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
        self.spinner.start("Plotting individual amplitudes")
        for wave in self.waves:
            self.plot_wave(wave, tag, err_tag)
        self.spinner.succeed()
        if self.pos_amplitudes:
            self.spinner.start("Plotting all amplitudes with positive reflectivity together")
            self.plot_amps(self.pos_amplitudes, "Positive Reflectivity", tag, err_tag)
            self.spinner.succeed()
        if self.neg_amplitudes:
            self.spinner.start("Plotting all amplitudes with negative reflectivity together")
            self.plot_amps(self.neg_amplitudes, "Negative Reflectivity", tag, err_tag)
            self.spinner.succeed()
        self.spinner.start("Plotting all amplitudes together")
        fig = plt.figure()
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown", "tab:pink", "tab:olive", "tab:cyan"]
        for i, amp in enumerate(self.pos_amplitudes):
            plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='o',
                            color=colors[i],
                            label=Plotter.get_label_from_amplitude(amp, refl=True))
        for i, amp in enumerate(self.neg_amplitudes):
            plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                            self.best_fit_df[amp + tag],
                            yerr=self.best_fit_df[amp + err_tag],
                            elinewidth=0.5,
                            fmt='s',
                            color=colors[i],
                            label=Plotter.get_label_from_amplitude(amp, refl=True))
        plt.errorbar(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                        self.best_fit_df['total' + tag],
                        yerr=self.best_fit_df['total' + err_tag],
                        elinewidth=0.5,
                        fmt='none',
                        color='k')
        plt.hist(self.bin_info_df['Centers'].iloc[self.best_fit_df['Bin']],
                    bins=len(self.bin_info_df),
                    range=(self.bin_info_df[self.bin_type].iloc[0],
                        self.bin_info_df[self.bin_type].iloc[-1]),
                    weights=self.best_fit_df['total' + tag],
                    fill=False,
                    histtype='step',
                    color='k',
                    label="Total")
        plt.title("All Amplitudes")
        plt.ylim(bottom=0)
        span = self.bin_info_df['Centers'].iloc[-1] - self.bin_info_df['Centers'].iloc[0]
        buf = span * 0.13
        plt.xlim(self.bin_info_df['Centers'].iloc[0] - buf,
                    self.bin_info_df['Centers'].iloc[-1] + buf)
        plt.ylabel("Intensity")
        plt.xlabel(self.xlabel)
        plt.legend()
        plt.tight_layout()
        self.pdf.savefig(fig, dpi=300)
        plt.close()
        self.spinner.succeed("Finished plotting intensities!")
