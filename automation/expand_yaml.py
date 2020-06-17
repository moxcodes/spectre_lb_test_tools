#!/bin/env python3

import os
import re
import sys
import numpy as np


# we use the yaml key string #< and #> to indicate an expanded list, if
# separated by commas, and a range object if separated with colons. Note
# that this will parse disasterously badly if a complicated expression is
# used, so don't...
def expand_yaml_string(string):
    if "#<" not in string:
        return [["", string]]
    pre_expansion = string.split("#<")[0]
    first_expansion = "".join(
        string.split("#<")[1].split("#>")[0].split('#\n'))
    post_expansion = string[len(pre_expansion) + 4 + len(first_expansion):]
    if "#!" in first_expansion:
        tag = first_expansion.split("#!")[1].split("#!")[0]
        all_expansions = [
            x.split("#>")[0] for x in string.split("#!" + tag + "#!")[1:]
        ]
        remaining_strings = string.split("#!" + tag + "#!")
        for i in range(1, len(remaining_strings)):
            remaining_strings[i] = "".join(
                remaining_strings[i].split("#>")[1:])
        for i in range(len(remaining_strings) - 1):
            remaining_strings[i] = remaining_strings[i][:-2]
    else:
        all_expansions = [first_expansion]
        remaining_strings = [pre_expansion, post_expansion]
    label = ""
    label_index = 0
    all_expansion_lists = []
    length = -1
    for i in range(len(all_expansions)):
        current_expansion = all_expansions[i]
        if '#"' in current_expansion:
            if label == "":
                label = current_expansion.split('#"')[1]
                label_index = i
            current_expansion = current_expansion.split('#"')[2]
        if "#," in current_expansion:
            expansion_list = current_expansion.split('#,')
        elif '#:' in current_expansion:
            range_information = current_expansion.split('#:')
            if '.' in range_information[0] or '.' in range_information[
                    1] or '.' in range_information[2]:
                expansion_list = list(
                    range(float(range_information[0]),
                          float(range_information[1]),
                          float(range_information[2])))
            else:
                expansion_list = list(
                    range(int(range_information[0]), int(range_information[1]),
                          int(range_information[2])))
        else:
            raise RuntimeError("unexpected expansion string: " +
                               current_expansion)
        if length == -1:
            length = len(expansion_list)
        elif length != len(expansion_list):
            raise RuntimeError("All lists with the same label must be equal " +
                               "lengths")
        all_expansion_lists += [expansion_list]

    expansion_result = []
    for expression_combination in np.transpose(np.array(all_expansion_lists)):
        assembled_string = ""
        for i in range(len(all_expansion_lists)):
            assembled_string += remaining_strings[i]
            assembled_string += str(expression_combination[i])
        assembled_string += remaining_strings[-1]
        print(assembled_string)
        for subexpansion in expand_yaml_string(assembled_string):
            print(subexpansion)
            expansion_result += [[
                label + "_" + str(expression_combination[label_index]) + "_" +
                subexpansion[0], subexpansion[1]
            ]]
    return expansion_result


# TODO consider different expansion 'modes' to support a wider varienty of run
# sets
def create_expanded_yaml_files(filename):
    parent_directory = os.path.dirname(filename)
    if parent_directory == "":
        parent_directory = "."
    with open(filename, "r") as meta_yaml_file:
        meta_string = meta_yaml_file.read()
    expanded_yaml_list = expand_yaml_string(meta_string)
    # now we need to replace the output file in each of the strings with
    # something sensible and write each one to file.
    for meta_yaml_entry in expanded_yaml_list:
        new_yaml_input = re.sub(
            r'VolumeFileName: "(.*)"\n',
            r'VolumeFileName: "' + meta_yaml_entry[0] + r'\1"\n',
            meta_yaml_entry[1])
        new_yaml_input = re.sub(
            r'ReductionFileName: "(.*)"\n',
            r'ReductionFileName: "' + meta_yaml_entry[0] + r'\1"\n',
            new_yaml_input)
        with open(
                parent_directory + "/" + meta_yaml_entry[0] +
                filename.split("/")[-1].split(".")[0] + ".yaml",
                "x") as new_yaml:
            new_yaml.write(new_yaml_input)


if __name__ == "__main__":
    create_expanded_yaml_files(sys.argv[1])
