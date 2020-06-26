import sys
import numpy as np
import subprocess
import networkx as nx
import load_balancing_test_tools.utilities.file_management as fm
import load_balancing_test_tools.utilities.CommGraphInfo as gi
import matplotlib.pyplot as plt
import matplotlib


def parse_user_defined_projections_to_dict_graph(projections_file,
                                                 dict_graph_list):
    # unzip it if it's a gz.
    if (projections_file[-3:] == ".gz"):
        subprocess.run(["gunzip", "-k", "-f", projections_file])
        projections_file = projections_file[:-3]
    print(projections_file)
    # iterate through the lines and record in the dict
    with open(projections_file, 'r') as f:
        file_contents = f.read().split('\n')
    i = 0
    # note: this currently assumes that there is only one graph tag to find.In
    # future, this will need to parse into several graphs.

    # Here we make the simplifying assumption that we will only log clock
    # events associated with the span represented by the graph dump.
    # This might be somewhat skewed due to the cost of the dump itself...
    clock_start = None
    global_clock_start = None
    global_clock_end = None
    current_from_component = None
    current_graph_index = None
    while i < len(file_contents):
        # the 'begin processing flag' -- tells us about the current
        if file_contents[i][:2] == "2 ":
            clock_start = int(file_contents[i].split(" ")[3])
        if file_contents[i][:2] == "3 " and clock_start is not None:
            clock_diff = int(file_contents[i].split(" ")[3]) - clock_start
            if current_from_component is not None:
                if global_clock_start is None:
                    global_clock_start = clock_start
                global_clock_end = int(file_contents[i].split(" ")[3])
                dict_graph_list[current_graph_index][
                    current_from_component].add_clock_ticks(clock_diff)
                current_from_component = None

        if file_contents[i][:2] == "26" and file_contents[i][3:5] == "-1":
            data_packet = []
            i += 1
            while not (file_contents[i][:2] == "26"
                       and file_contents[i][3:5] == "-2"):
                data_packet += [file_contents[i].split(" ")[1]]
                i += 1
            dim = int((len(data_packet) - 3) / 2)
            if current_graph_index is not None and int(
                    data_packet[0]) != current_graph_index:
                for key in dict_graph_list[current_graph_index]:
                    print("key: " + str(key))
                    dict_graph_list[current_graph_index][
                        key].record_global_ticks(global_clock_end -
                                                 global_clock_start)
                global_clock_start = None
                global_clock_end = None
                current_from_component = None
            current_graph_index = int(data_packet[0])
            if len(dict_graph_list) <= current_graph_index:
                dict_graph_list += [{}]

            from_component_tag = gi.ComponentTag(":".join(data_packet[2:(dim +
                                                                         3)]))
            to_component_tag = gi.ComponentTag(":".join(
                data_packet[(dim + 3):(2 * dim + 4)]))
            print("from component")
            print(str(from_component_tag))
            print("to component")
            print(str(to_component_tag))
            print("insert? " + str(
                from_component_tag in dict_graph_list[current_graph_index]))
            if from_component_tag in dict_graph_list[current_graph_index]:
                dict_graph_list[current_graph_index][
                    from_component_tag].insert_neighbor(
                        gi.BidirectionalEdgeInfo(from_component_tag,
                                                 to_component_tag))
            else:
                print("inserting new")
                dict_graph_list[current_graph_index][
                    from_component_tag] = gi.GraphElementInfo(
                        from_component_tag, int(data_packet[1]),
                        gi.BidirectionalEdgeInfo(from_component_tag,
                                                 to_component_tag))
                print("insert? " + str(from_component_tag in
                                       dict_graph_list[current_graph_index]))
            current_from_component = from_component_tag
        else:
            i += 1

    for key in dict_graph_list[current_graph_index]:
        print("key: " + str(key))
        dict_graph_list[current_graph_index][key].record_global_ticks(
            global_clock_end - global_clock_start)
    return dict_graph_list


def collapse_graph(dict_graph):
    previous_size = len(dict_graph) + 1
    while (len(dict_graph) != previous_size):
        previous_size = len(dict_graph)
        print("collapsing iteration start")
        for key in dict_graph:
            print("trying to collapse " + str(key))
            next_nodes = dict_graph[key].neighbors
            breaking_out = False
            for node in next_nodes:
                print("considering: " + str(node.other(key)))
                if dict_graph[node.other(key)].pe == dict_graph[key].pe:
                    other_key = node.other(key)
                    print("merging: " + str(other_key))
                    dict_graph[key].merge_in_component_set(
                        dict_graph[other_key].merged_component_set)
                    dict_graph[key].add_clock_ticks(
                        dict_graph[other_key].element_clock_ticks)
                    for edge in dict_graph[other_key].neighbors:
                        for neighbor_edge in dict_graph[edge.other(
                                other_key)].neighbors:
                            neighbor_edge.reassign(other_key, key)
                        edge.reassign(other_key, key)
                        dict_graph[key].insert_neighbor(edge)

                    for edge in dict_graph[key].neighbors:
                        if edge.other(key) == other_key:
                            dict_graph[key].neighbors.remove(edge)
                    for edge in dict_graph[key].neighbors:
                        if edge.other(key) == key:
                            dict_graph[key].neighbors.remove(edge)
                    dict_graph.pop(other_key)
                    breaking_out = True
                    break
            if breaking_out:
                break
    return dict_graph


def plot_communication_graph(projections_dir, output_file):
    dict_graph_list = [{}]
    projections_logs = fm.find_files(projections_dir, "*\.log\.gz")
    for projection_log in projections_logs:
        parse_user_defined_projections_to_dict_graph(projection_log,
                                                     dict_graph_list)
    dict_graph_index = 0
    for dict_graph in dict_graph_list:
        collapse_graph(dict_graph)
        print("graph size:")
        print(len(dict_graph))
        G = nx.Graph()
        labels = {}
        node_sizes = []

        node_avg_loads = []
        node_colors = []

        coms_per_element = []
        node_border_colors = []
        for key in dict_graph:
            G.add_node(key, pe=dict_graph[key].pe)
            labels[key] = str(dict_graph[key].pe)
            print(labels[key])

        print()
        for node in G.nodes():
            print(len(dict_graph[node].merged_component_set))
            node_sizes += [
                len(dict_graph[node].merged_component_set) * 1500 /
                np.sqrt(len(dict_graph))
            ]
            node_avg_loads += [
                dict_graph[node].load_portion() /
                len(dict_graph[node].merged_component_set)
            ]
            total_coms = 0
            for edge in dict_graph[node].neighbors:
                total_coms += edge.weight
            coms_per_element += [
                total_coms / len(dict_graph[node].merged_component_set)
            ]

        max_avg_load = max(node_avg_loads)
        max_coms_per_element = max(coms_per_element)
        # TODO create a color legend
        for node_avg_load in node_avg_loads:
            node_colors += [
                matplotlib.colors.to_hex([
                    1.0 * (node_avg_load / max_avg_load), 0.0,
                    1.0 * (1.0 - node_avg_load / max_avg_load)
                ])
            ]
        for coms in coms_per_element:
            node_border_colors += [
                matplotlib.colors.to_hex([
                    0.0, 1.0 * (1.0 - coms / max_coms_per_element),
                    1.0 * (coms / max_coms_per_element)
                ])
            ]

        edge_set = set()
        for key in dict_graph:
            for edge in dict_graph[key].neighbors:
                if edge not in edge_set:
                    G.add_edge(edge.first_component,
                               edge.second_component,
                               weight=edge.weight)
                    edge_set.add(edge)

        edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
        pos = nx.spring_layout(G,
                               k=1 / np.sqrt(len(G.nodes()) * 4),
                               iterations=500,
                               threshold=1e-8)
        nx.draw(G,
                pos=pos,
                node_size=node_sizes,
                node_color=node_colors,
                edgecolors=node_border_colors,
                linewidths=3.0,
                width=edge_weights)
        nx.draw_networkx_labels(G, pos, labels)
        if output_file[-4:] == ".pdf":
            plt.savefig(output_file[:-4] + "_" + str(dict_graph_index) +
                        ".pdf")
        else:
            plt.savefig(output_file + "_" + str(dict_graph_index) + ".pdf")
        plt.clf()
        dict_graph_index += 1


if __name__ == "__main__":
    plot_communication_graph(sys.argv[1], sys.argv[2])
