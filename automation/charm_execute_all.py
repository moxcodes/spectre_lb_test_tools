#!/bin/env python3

import os
import re
import sys
import subprocess
import numpy as np


dry_run = True


def execute_all_in_sequence(directory):
    # get all the yaml files in the directory
    yaml_list = subprocess.check_output(["find", ".", "-name", "'*\.yaml'"
                                         ]).decode().split('\n')[:-1]
    for job_filename in yaml_list:
        with open(job_filename, 'r') as f:
            file_contents = f.readlines()
        if "# EXECUTABLE_STRING=" not in file_contents:
            raise RuntimeError("EXECUTABLE_STRING not found")
        executable_string = file_contents.split(
            "# EXECUTABLE_STRING")[1].split("\n")[0].lstrip().rstrip()
        if dry_run:
            print("dry run; would have executed:")
            print(executable_string.split(" "))
        else:
            subprocess.run(executable_string.split(" "))


if __name__ == "__main__":
    # TODO: at some point, this should be generalized to a
    #  better job-farming strategy, but for now we'll just
    # run the jobs one by one.
    execute_all_in_sequence(sys.argv[1])
