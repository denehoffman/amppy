#!/usr/bin/env python3

import sys
import subprocess
import rcdb
from pathlib import Path
import re
import argparse
import pandas as pd
import os
import shutil
import errno
from datetime import datetime

def main():
    start_time = datetime.now()
    parser = argparse.ArgumentParser(prog="root_to_amptools",
                                     description="Provides a pathway to convert a directory of ROOT files to AmpTools flat trees divided by polarization")
    parser.add_argument("directory", help="the input directory containing ROOT files")
    parser.add_argument("-o", "--output", help="the output directory for the merged files")
    parser.add_argument("-f", "--format", help="format of ROOT input files, use # as a wildcard")
    args = parser.parse_args()

    file_format = "*.root"
    if not args.format is None:
        file_format = args.format.replace("#","*")

    input_dir = Path(args.directory).resolve()
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        output_dir = input_dir

    if not input_dir.is_dir():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(input_dir))
    if not output_dir.is_dir():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(output_dir))
    merge(input_dir, output_dir, file_format)
    dselector = Path(args.dselector).resolve()
    if not dselector.suffix:
        dselector = Path(str(dselector) + ".C")
    if dselector.suffix == ".h":
        dselector = Path(str(dselector).replace(".h", ".C"))
    end_time = datetime.now()
    print(f"Finished! Time Elapsed: {str(end_time-start_time)}")


def merge(input_dir, output_dir, file_format):
    db = rcdb.RCDBProvider("mysql://rcdb@hallddb.jlab.org/rcdb")
    input_files = list(input_dir.glob(file_format))
    input_run_numbers = []
    input_file_tuples = []
    error_files = []
    for f in input_files:
        number_regex = re.search("(\d{6})", f.name)
        if number_regex:
            run_number = int(number_regex.group(1))
            input_run_numbers.append(run_number)
            input_file_tuples.append((f, run_number))
        else:
            error_files.append(f)
    if len(error_files):
        print("The following files did not match the usual RegEx (\d{6}):")
        for f in error_files:
            print(f.name)
        response = input("Would you like to continue without these files? (Y/n)")
        if not (response == "y" or response == "Y"):
            sys.exit(1)
    max_run_number = max(input_run_numbers)
    min_run_number = min(input_run_numbers)
    print(f"{len(input_file_tuples)} files found with run numbers between {min_run_number} and {max_run_number}")
    print("Accessing the RCDB to get a list of approved production runs...")
    if max_run_number < 40000:
        production_query = "@is_production and @status_approved"
    elif max_run_number < 60000:
        production_query = "@is_2018production and @status_approved"
    elif min_run_number > 70000:
        production_query = "@is_dirc_production and @status_approved"
    else:
        print("Error! It's possible that some run numbers overlap multiple run periods or you are choosing runs between 60,000 and 70,000")
        sys.exit(1)
    rcdb_runs = db.select_runs(production_query, run_min=min_run_number, run_max=max_run_number)
    print(f"Query Complete! Time Elapsed:")
    print(f"\tPrep time:\t{round(rcdb_runs.performance['preparation'], 4)}s")
    print(f"\tQuery Time:\t{round(rcdb_runs.performance['query'], 4)}s")
    print(f"\tSelection Time:\t{round(rcdb_runs.performance['selection'], 4)}s")
    
    print(f"Tabulating run info...")
    rcdb_table = rcdb_runs.get_values(['polarization_angle'], insert_run_number=True)
    print(f"Tabulation Complete! Time Elapsed: {round(rcdb_runs.performance['tabling_values'], 4)}s")
    AMO_files = []
    PARA_0_files = []
    PARA_135_files = []
    PERP_45_files = []
    PERP_90_files = []
    rcdb_run_numbers = [row[0] for row in rcdb_table]
    for root_file, run_number in input_file_tuples:
        try:
            row = rcdb_table[rcdb_run_numbers.index(run_number)]
            if row[1] == -1.0:
                AMO_files.append(root_file)
            elif row[1] == 0.0:
                PARA_0_files.append(root_file)
            elif row[1] == 45.0:
                PERP_45_files.append(root_file)
            elif row[1] == 90.0:
                PERP_90_files.append(root_file)
            elif row[1] == 135.0:
                PARA_135_files.append(root_file)
            else:
                print(f"An error occurred with file {root_file.name} which has polarization angle = {row[1]}")
        except:
            print(f"File {root_file.name} with run number {run_number} not matched in RCDB")

    print(f"Found {len(AMO_files)} AMO files")
    print(f"Found {len(PARA_0_files)} 0 deg PARA files")
    print(f"Found {len(PERP_45_files)} 45 deg PERP files")
    print(f"Found {len(PERP_90_files)} 90 deg PERP files")
    print(f"Found {len(PARA_135_files)} 135 deg PARA files")
    print("Merging...")
    print("Merging AMO...")
    subprocess.run(['hadd', '-f', str(output_dir / f"tree_sum_AMO_{min_run_number}_{max_run_number}.root")] + [str(f) for f in AMO_files])
    print("Merging PARA 0...")
    subprocess.run(['hadd', '-f', str(output_dir / f"tree_sum_PARA_0_{min_run_number}_{max_run_number}.root")] + [str(f) for f in PARA_0_files])
    print("Merging PERP 45...")
    subprocess.run(['hadd', '-f', str(output_dir / f"tree_sum_PERP_45_{min_run_number}_{max_run_number}.root")] + [str(f) for f in PERP_45_files])
    print("Merging PERP 90...")
    subprocess.run(['hadd', '-f', str(output_dir / f"tree_sum_PERP_90_{min_run_number}_{max_run_number}.root")] + [str(f) for f in PERP_90_files])
    print("Merging PARA 135...")
    subprocess.run(['hadd', '-f', str(output_dir / f"tree_sum_PARA_135_{min_run_number}_{max_run_number}.root")] + [str(f) for f in PARA_135_files])
    print("Merging Complete!")


if __name__ == "__main__":
    main()
