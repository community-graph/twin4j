import glob

import re


def find_featured_community_member(lines):
    for idx, line in enumerate(lines):
        matches = re.match("=== Featured Community Member(s)?:", line)
        if matches:
            return idx
    return -1


def filter_lines(lines):
    filtered_lines = []
    exclude = False
    for line in lines:
        if line.startswith("++++"):
            if exclude:
                exclude = False
            else:
                exclude = True
        if not exclude:
            filtered_lines.append(line)

    return filtered_lines


paths = glob.glob("/Users/markneedham/projects/twin4j/adoc/*.adoc")

for path in paths:
    with open(path, "r") as twin4j_file:
        lines = twin4j_file.readlines()

        lines = [line for line in filter_lines(lines) if len(line.strip()) > 0]

        index = find_featured_community_member(lines)

        potential = lines[index + 1: index + 10]

        valid_lines = [line for line in potential
                       if "twitter" in line or "linkedin" in line or "featured community member" in line]

        for line in valid_lines:
            matches = re.match("(https?://.*)\[(.*)\^?\]", line)
            print(line, matches)
