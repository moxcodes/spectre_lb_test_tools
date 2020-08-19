#!/bin/env python3


class ComponentTag:
    def __init__(self, tag_string):
        self.tag_string = tag_string
        split_tag_string = tag_string.split(":")
        self.component_id = int(split_tag_string[0])
        self.block_index = []
        self.element_index = []
        self.refinement_level = []
        for segment_id in split_tag_string[1:]:
            binary_string = format(int(segment_id), '#034b')
            self.block_index += [int(binary_string[2:9])]
            self.refinement_level += [int(binary_string[9:14])]
            self.element_index += [int(binary_string[14:34])]

    def __str__(self):
        return self.tag_string

    def __hash__(self):
        return hash(self.tag_string)

    def __lt__(self, other):
        return self.tag_string < other.tag_string

    def __eq__(self, other):
        return self.tag_string == other.tag_string

    def __ne__(self, other):
        return self.tag_string != other.tag_string


class BidirectionalEdgeInfo:
    def __init__(self, from_component_tag, to_component_tag, weight=1):
        self.weight = weight
        tags = [from_component_tag, to_component_tag]
        tags.sort()
        self.first_component = tags[0]
        self.second_component = tags[1]

    def other(self, component_tag):
        if (self.first_component == component_tag):
            return self.second_component
        elif (self.second_component == component_tag):
            return self.first_component
        else:
            raise RuntimeError("other call in edge is ambiguous")

    def reassign(self, previous, new):
        if self.first_component == previous:
            self.first_component = new
        if self.second_component == previous:
            self.second_component = new
        tags = [self.first_component, self.second_component]
        tags.sort()
        self.first_component = tags[0]
        self.second_component = tags[1]
        return

    def __eq__(self, other):
        return self.first_component == other.first_component\
          and self.second_component == other.second_component

    def __ne__(self, other):
        return self.first_component != other.first_component\
          or self.second_component != other.second_component

    def __hash__(self):
        return hash(self.first_component.tag_string +
                    self.second_component.tag_string)


class GraphElementInfo:
    def __init__(self, component_tag, pe, first_neighbor=None):
        self.component_tag = component_tag
        self.merged_component_set = set([component_tag])
        self.pe = pe
        self.neighbors = []
        self.element_clock_ticks = 0
        self.global_clock_ticks = 0
        if first_neighbor is not None:
            self.neighbors += [first_neighbor]

    # 'bundles' duplicate edges into weights
    def insert_neighbor(self, neighbor):
        for local_neighbor in self.neighbors:
            if (local_neighbor.first_component == neighbor.first_component
                    and local_neighbor.second_component ==
                    neighbor.second_component):
                local_neighbor.weight += neighbor.weight
                return
        self.neighbors += [neighbor]

    def merge_in_component_set(self, merging_set):
        self.merged_component_set = self.merged_component_set.union(
            merging_set)

    def add_clock_ticks(self, ticks):
        self.element_clock_ticks += ticks

    def record_global_ticks(self, ticks):
        self.global_clock_ticks = ticks

    def load_portion(self):
        return self.element_clock_ticks / self.global_clock_ticks
