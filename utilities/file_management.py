#!/bin/env python3

import subprocess
import yaml
import os


def find_files(directory, string):
    return subprocess.check_output(["find", directory, "-name",
                                    string]).decode().split('\n')[:-1]


def get_time_from_charm_stdout(filename):
    with open(filename, "r") as charm_stdout:
        for line in charm_stdout:
            if "WallTimer" in line:
                return float(line.split("seconds")[-1].rstrip().lstrip())


# TODO consider methods of combining these functions to avoid code duplication


def get_communication_load(yaml_file):
    with open(yaml_file, "r") as f:
        yaml_data = yaml.safe_load(f)
        return int(yaml_data.get("TestLoadBalancing").get('CommunicationSize'))


def get_distribution_strategy(yaml_file):
    with open(yaml_file, "r") as f:
        yaml_data = yaml.safe_load(f)
        return yaml_data.get("TestLoadBalancing").get("DistributionStrategy")


# note that this isn't actually encoded in the yaml so we just have to trust
# that this has been run in such a way that the execution string is specified.
def get_number_of_processors(yaml_file):
    with open(yaml_file, 'r') as f:
        file_contents = "".join(f.readlines())
        if "# EXECUTABLE_STRING=" not in file_contents:
            raise RuntimeError(
                "EXECUTABLE_STRING not found, cannot determine number of" +
                " processors used")
        executable_string = file_contents.split(
            "# EXECUTABLE_STRING=")[1].split("\n")[0].lstrip().rstrip()
        # this makes a lot of format assumptions, but it's probably the
        # easiest thing to do that is even a little general.
        return int(
            executable_string.split("+ppn")[-1].split("+p")[-1].split(" ")[0])
