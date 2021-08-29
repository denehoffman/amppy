from FitResults import FitResultsWrapper
import sys

def get_likelihood(fit_file):
    wrapper = FitResultsWrapper(fit_file)
    print(wrapper.likelihood())
    print(wrapper.total_intensity(True))
    amps = sys.argv[2:]
    print(wrapper.intensity(amps, True))
    print(wrapper.phaseDiff(*amps))


if __name__ == "__main__":
    get_likelihood(sys.argv[1])
