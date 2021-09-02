from amppy.plotting.Plotter import Plotter
import argparse
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from halo import Halo

class Plotter_Intensity(Plotter):
    @staticmethod
    def plotter_description():
        return ("Plot Amplitudes", "Plots amplitudes on the complex plane for each bin") 

    @staticmethod
    def configure(kwdict):
        if not "plot_contours" in kwdict:
            kwdict["plot_contours"] = input("Plot contours on amplitude plots? (y/n)\n> ") == 'y'
        if not "plot_density" in kwdict:
            kwdict["plot_density"] = input("Plot density on amplitude plots? (y/n)\n> ") == 'y'
        return kwdict

    def plot(self, kwdict):
        plt.rcParams["figure.figsize"] = (10 * len(self.waves), 20)
        plt.rcParams["font.size"] = 24
        self.spinner.start(f"Plotting Amplitudes for Bin 0")
        for bin_num in range(len(self.bin_info_df)):
            fig, axes = plt.subplots(nrows=2, ncols=len(self.waves))
            fits_in_bin_df = self.fits_in_bin[bin_num]
            for i, wave in enumerate(self.waves):
                amp = wave + "+"
                if amp in self.amplitudes:
                    xmin, ymin = fits_in_bin_df[[amp + "_AMP_re", amp + "_AMP_im"]].agg('min').to_list()
                    xmax, ymax = fits_in_bin_df[[amp + "_AMP_re", amp + "_AMP_im"]].agg('max').to_list()
                    x_range = max(max(abs(xmax), abs(xmin)), 1)
                    y_range = max(max(abs(ymax), abs(ymin)), 1)
                    try: # Credit to Flabetvibes at https://stackoverflow.com/a/30146280 for this code
                        xx, yy = np.mgrid[-x_range:x_range:100j, -y_range:y_range:100j]
                        positions = np.vstack([xx.ravel(), yy.ravel()])
                        values = np.vstack([
                            fits_in_bin_df.loc[:, amp + "_AMP_re"],
                            fits_in_bin_df.loc[:, amp + "_AMP_im"]
                        ])
                        kdernel = st.gaussian_kde(values)
                        f = np.reshape(kernel(positions).T, xx.shape)
                        if kwdict.get("plot_contours"):
                            axes[0, i].contour(xx, yy, f, levels=4, colors='k')
                        if kwdict.get("plot_density"):
                            axes[0, i].contourf(xx, yy, f, levels=4, colors='Blues')
                    except:
                        pass
                    axes[0, i].scatter(fits_in_bin_df.loc[:, amp + "_AMP_re"],
                                        fits_in_bin_df.loc[:, amp + "_AMP_im"],
                                        color='k',
                                        marker=',')
                    axes[0, i].scatter(self.best_fit_df.loc[self.best_fit_df['Bin'] == bin_num][amp + "_AMP_re"],
                                        self.best_fit_df.loc[self.best_fit_df['Bin'] == bin_num][amp + "_AMP_im"],
                                        color='r',
                                        marker='o')
                    axes[0, i].set_xlabel("Re")
                    axes[0, i].set_ylabel("Im")
                    axes[0, i].set_xlim(-x_range, x_range)
                    axes[0, i].set_ylim(-y_range, y_range)
                    axes[0, i].set_title(Plotter.get_label_from_amplitude(amp, refl=True))
                amp = wave + "-"
                if amp in self.amplitudes:
                    xmin, ymin = fits_in_bin_df[[amp + "_AMP_re", amp + "_AMP_im"]].agg('min').to_list()
                    xmax, ymax = fits_in_bin_df[[amp + "_AMP_re", amp + "_AMP_im"]].agg('max').to_list()
                    x_range = max(max(abs(xmax), abs(xmin)), 1)
                    y_range = max(max(abs(ymax), abs(ymin)), 1)
                    try: # Credit to Flabetvibes at https://stackoverflow.com/a/30146280 for this code
                        xx, yy = np.mgrid[-x_range:x_range:100j, -y_range:y_range:100j]
                        positions = np.vstack([xx.ravel(), yy.ravel()])
                        values = np.vstack([
                            fits_in_bin_df.loc[:, amp + "_AMP_re"],
                            fits_in_bin_df.loc[:, amp + "_AMP_im"]
                        ])
                        kdernel = st.gaussian_kde(values)
                        f = np.reshape(kernel(positions).T, xx.shape)
                        if kwdict.get("plot_contours"):
                            axes[1, i].contour(xx, yy, f, levels=4, colors='k')
                        if kwdict.get("plot_density"):
                            axes[1, i].contourf(xx, yy, f, levels=4, colors='Blues')
                    except:
                        pass
                    axes[1, i].scatter(fits_in_bin_df.loc[:, amp + "_AMP_re"],
                                        fits_in_bin_df.loc[:, amp + "_AMP_im"],
                                        color='k',
                                        marker=',')
                    axes[1, i].scatter(self.best_fit_df.loc[self.best_fit_df['Bin'] == bin_num][amp + "_AMP_re"],
                                        self.best_fit_df.loc[self.best_fit_df['Bin'] == bin_num][amp + "_AMP_im"],
                                        color='r',
                                        marker='o')
                    axes[1, i].set_xlabel("Re")
                    axes[1, i].set_ylabel("Im")
                    axes[1, i].set_xlim(-x_range, x_range)
                    axes[1, i].set_ylim(-y_range, y_range)
                    axes[0, i].set_title(Plotter.get_label_from_amplitude(amp, refl=True))
            fig.suptitle(f"Bin {bin_num} {self.bin_info_df['Label'].iloc[bin_num]} Fit Amplitude Distributions")
            plt.tight_layout()
            self.pdf.savefig(fig, dpi=300)
            plt.close()
            self.spinner.text = f"Plotting Amplitudes for Bin {bin_num}"
        self.spinner.succeed("Plotted Amplitudes!")
