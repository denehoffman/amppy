from amppy.plotting.Plotter import Plotter
import argparse
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from halo import Halo
import numpy as np
from amppy import utilities
import collections

class Plotter_BW(Plotter):

    @staticmethod
    def plotter_description():
        return ("Plot Breit-Wigners", "Plots Resonances (Mass Dependent fits only)")

    @staticmethod
    def configure(kwdict):
        if not "acceptance_corrected" in kwdict:
            kwdict["acceptance_corrected"] = input("Use acceptance corrected values? (y/n)\n> ") == 'y'
        if not "xlabel_invmass" in kwdict:
            particles = input("Input the x-axis label to be used for the invariant mass (example: 'K_SK_S' for two K-short particles)\n> ")
            kwdict["xlabel_invmass"] = f"m$({particles})$ GeV/$c^2$"
        return kwdict

    def plot_amps(self, bw_dict, tag, err_tag, acc=True):
        fig = plt.figure()
        sub_info, data_info, bkg_info, gen_info, acc_info = self.get_mass_distribution()
        if acc:
            gen_hist, bin_edges = np.histogram(gen_info[0], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=gen_info[1])
            acc_hist, _ = np.histogram(acc_info[0], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=acc_info[1])
            data_hist, _ = np.histogram(data_info[0], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=data_info[1])
            bkg_hist, _ = np.histogram(bkg_info[0], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=bkg_info[1])
            sub_hist, _ = np.histogram(sub_info[0], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=sub_info[1])
            sub_hist_corr = sub_hist * gen_hist / acc_hist * 1500 # arbitrary scale for now
            data_hist_corr = data_hist * gen_hist / acc_hist * 1500 # arbitrary scale for now
            bkg_hist_corr = bkg_hist * gen_hist / acc_hist * -1500 # arbitrary scale for now
            plt.hist(bin_edges[:-1], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=sub_hist_corr, fill=False, histtype='step', label="Subtracted")
            plt.hist(bin_edges[:-1], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=data_hist_corr, fill=False, histtype='step', label="Data")
            plt.hist(bin_edges[:-1], range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=bkg_hist_corr, fill=False, histtype='step', label="Background")
        else:
            plt.hist(dmass, range=(self.bin_edges[0], self.bin_edges[-1]), bins=80, weights=np.array(dweight)*2000) # arbitrary scale
        m = np.linspace(self.bin_edges[0], self.bin_edges[1], 2000) 
        z_all_amps = 0
        for amp, bw in bw_dict.items():
            z_amp = (self.best_fit_df[amp + "_AMP_re"] + 1j * self.best_fit_df[amp + "_AMP_im"]).to_numpy()
            z_bw = np.array(bw.f(m))
            z_tot = z_amp * np.array(bw.f(m))
            z_all_amps += z_tot
            plt.plot(m, np.power(np.abs(z_tot), 2), label=amp[:-2])
        plt.plot(m, np.power(np.abs(z_all_amps), 2), label="Coherent Total")
        plt.legend()
        plt.tight_layout()
        self.pdf.savefig(fig, dpi=300)
        plt.close()


    def plot(self, kwdict):
        bw_dict = {}
        with open(self.config_template) as cfg:
            lines = cfg.readlines()
            for line in lines:
                if line.startswith("amplitude") and "PositiveRe" in line and "BreitWigner" in line:
                    reaction, _, amp_name, _, BW = utilities.parse_amplitude(line)
                    bw_dict[amp_name] = BW
        plt.rcParams["figure.figsize"] = (20, 10)
        plt.rcParams["font.size"] = 24
        if kwdict.get("acceptance_corrected"):
            tag = "_AC_INT"
            err_tag = "_AC_INT_err"
        else:
            tag = "_NC_INT"
            err_tag = "_NC_INT_err"
        self.xlabel = kwdict.get("xlabel_invmass")
        self.spinner.start("Plotting Breit-Wigners")
        if not bw_dict:
            self.spiner.fail(f"No Breit-Wigner amplitudes found in {str(self.config_template)}!")
            return
        self.plot_amps(bw_dict, tag, err_tag, kwdict.get("acceptance_corrected"))
        self.spinner.succeed()

