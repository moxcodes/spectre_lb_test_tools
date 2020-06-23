import sys
import numpy as np
import matplotlib.pyplot as plt
import load_balancing_test_tools.utilities.file_management as fm
import load_balancing_test_tools.configuration.basic as cf

# In these tests, we vary:
# - communication load
# - number of processors
# - distribution strategy

# runtime as a function of processor number
# for each distribution strategy, for 3 choices
# of communication load (lowest, median, highest)


def get_load_balancing_runtime_data(directory):
    yaml_files = fm.find_files(directory, "*\.yaml")
    output_files = [x[:-4] + "out" for x in yaml_files]
    # get the set of communication loads and distribution
    # strategies
    com_loads = []
    dist_strategies = []
    for yaml_file in yaml_files:
        com_load = fm.get_communication_load(yaml_file)
        dist_strat = fm.get_distribution_strategy(yaml_file)
        if com_load not in com_loads:
            com_loads += [com_load]
        if dist_strat not in dist_strategies:
            dist_strategies += [dist_strat]
    # just take the smallest, largest, and median communication
    # loads for plot simplicity
    com_loads.sort()
    reduced_com_loads = [
        com_loads[0], com_loads[int(len(com_loads) / 2)], com_loads[-1]
    ]
    print(reduced_com_loads)
    plot_data = {}
    for yaml_file in yaml_files:
        com_load = fm.get_communication_load(yaml_file)
        dist_strat = fm.get_distribution_strategy(yaml_file)
        if com_load in reduced_com_loads:
            label_string = "Com: " + str(com_load) + ", Dist: " + dist_strat
            if label_string in plot_data:
                plot_data[label_string] += [[
                    fm.get_number_of_processors(yaml_file),
                    fm.get_time_from_charm_stdout(yaml_file[:-4] + "out")
                ]]
            else:
                plot_data[label_string] = [[
                    fm.get_number_of_processors(yaml_file),
                    fm.get_time_from_charm_stdout(yaml_file[:-4] + "out")
                ]]
    return plot_data


def plot_load_balancing_runtime_data(directory, destination):
    plot_data = get_load_balancing_runtime_data(directory)
    plt.rcParams["figure.figsize"] = 8, 4
    plt.title("Runtime comparisons for distribution strategies", fontsize=14)
    plt.xlabel("number of processors")
    plt.yscale('log')
    plt.ylabel("wall-clock runtime")
    legend = []
    i = 0
    for key in plot_data:
        data_entry = plot_data[key]
        data_entry.sort()
        legend += [key]
        transposed_data = np.transpose(np.array(data_entry))
        plt.plot(transposed_data[0],
                 transposed_data[1],
                 linestyle='--',
                 marker='.',
                 color=cf.colorwheel[i])
        i += 1
    plt.legend(legend,
               bbox_to_anchor=(1, 1),
               loc="upper left",
               borderaxespad=0)
    plt.tight_layout()
    plt.savefig(destination, dpi=400)
    plt.clf()


if __name__ == "__main__":
    plot_load_balancing_runtime_data(sys.argv[1], sys.argv[2])
