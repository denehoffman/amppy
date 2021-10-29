import numpy as np

class BreitWigner:
    def __init__(self, mass, width, *args):
        self.mass = mass
        self.width = width
        self.L = None
        self.mass1 = None
        self.mass2 = None
        if len(args) == 3:
            self.L = args[0]
            self.mass1 = args[1]
            self.mass2 = args[2]
        self.f = np.vectorize(self.f_novec)

    def f_novec(self, m):
        F = 1.0
        q_width = self.width
        if not self.L == None:
            q0 = np.abs(breakupMomentum(self.mass, self.mass1, self.mass2))
            q = np.abs(breakupMomentum(m, self.mass1, self.mass2))
            F0 = barrierFactor(q0, self.L)
            F = barrierFactor(q, self.L)
            q_width = self.width * (self.mass / m) * (q / q0) * (F / F0)**2
        numerator = np.sqrt(self.mass * self.width / np.pi)
        denominator = (self.mass**2 - m**2 - 1.0j * self.mass * q_width)
        return F * numerator / denominator
            
    
    def barrierFactor(q, spin):
        z = q**2 / (0.1973)**2
        if spin == 0:
            return 1.0
        elif spin == 1:
            return np.sqrt((2 * z) / (z + 1.0))
        elif spin == 2:
            return np.sqrt((13 * z**2) / ((z - 3)**2 + 9 * z))
        elif spin == 3:
            return np.sqrt((277 * z**3) / (z * (z - 15)**2 + 9 * (2 * z - 5)**2))
        elif spin == 4:
            return np.sqrt((12746 * z**4) / ((z**2 - 45 * z + 105)**2 + 25 * z * (2 * z - 21)**2))
        else:
            return 0.0
    
    def breakupMomentum(m, m1, m2):
        return np.sqrt(np.abs(m**4 + m1**4 + m2**4 - 2 * m**2 * m1**2 - 2 * m**2 * m2**2 - 2 * m1**2 * m2**2)) / (2 * m)

class Zlm:
    def __init__(self, L, M, refl):
        self.L = L
        self.M = M
        self.refl = refl


def parse_amplitude(line):
    parts = line.split(" ")
    amp_parts = parts[1].split("::")
    name_string = parts[2]
    reaction = amp_parts[0]
    summation = amp_parts[1]
    amplitude_name = amp_parts[2]
    if name_string == "Zlm":
        return reaction, summation, amplitude_name, name_string, Zlm(int(parts[3]), int(parts[4]), int(parts[5]) * int(parts[6]))
    if name_string == "BreitWigner":
        return reaction, summation, amplitude_name, name_string, BreitWigner(float(parts[3]), float(parts[4]), int(parts[5]), [int(parts[6]), int(parts[7])])
