#!/bin/env python3

import os
import re
import shlex
import sys
import subprocess
import numpy as np


dry_run = False


def execute_all_in_sequence(directory):
    os.chdir(directory)
    # get all the yaml files in the directory
    yaml_list = subprocess.check_output(["find", ".", "-name", "*\.yaml"
                                         ]).decode().split('\n')[:-1]
    print(yaml_list)
    for job_filename in yaml_list:
        with open(job_filename, 'r') as f:
            file_contents = "".join(f.readlines())
        if "# EXECUTABLE_STRING=" not in file_contents:
            raise RuntimeError("EXECUTABLE_STRING not found")
        executable_string = file_contents.split(
            "# EXECUTABLE_STRING=")[1].split("\n")[0].lstrip().rstrip()
        if dry_run:
            print("dry run; would have executed:")
            print(shlex.quote(executable_string))
        else:
            subprocess.run(shlex.quote(executable_string),
                           shell=True)


if __name__ == "__main__":
    # TODO: at some point, this should be generalized to a
    #  better job-farming strategy, but for now we'll just
    # run the jobs one by one.
    execute_all_in_sequence(sys.argv[1])
