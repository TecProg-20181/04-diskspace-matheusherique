#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import os
import subprocess
import re
from contracts import contract



# ==== Arguments ====

PARSER = argparse.ArgumentParser(
    description='Analizes and reports the disk usage per folder'
)
PARSER.add_argument('directory', metavar='DIR', type=str, nargs='?',
                    default='.', help='Directory to be analized')
PARSER.add_argument('-o', '--order', type=str, default='desc',
                    choices=['desc', 'asc'],
                    help='The file order inside each folder')
PARSER.add_argument('-s', '--hide', type=int, default=0,
                    help='Hides all files that have a percentage lower than '
                         'this value')
GROUP = PARSER.add_mutually_exclusive_group()
GROUP.add_argument('-a', '--all', help='Shows the full tree',
                   action='store_true')
GROUP.add_argument('-d', '--depth',
                   help='Specifies the folder maximum depth to be analyzed',
                   type=int, default=1)
PARSER.add_argument('-t', '--tree-view', action='store_true',
                    help='Display the result in a tree mode')

ARGS = PARSER.parse_args()


# ==== Disk Space ====

@contract
def subprocess_check_output(command):
    """ Function description.
        :type command: string
        :rtype: string
    """
    return subprocess.check_output(command.strip().split(' '))

@contract
def bytes_to_readable(blocks):
    """ Function description.
        :type command: int,>=0
        :rtype: string
    """
    byts = blocks * 512
    readable_bytes = byts
    count = 0
    while readable_bytes / 1024:
        readable_bytes /= 1024
        count += 1

    labels = ['B', 'Kb', 'Mb', 'Gb', 'Tb']
    return '{:.2f}{}'.format(round(byts/(1024.0**count), 2), labels[count])

@contract
def print_tree(file_tree, file_tree_node, path, largest_size, total_size,
               depth=0):
    """ Function description.
        :type file_tree='dict(string: dict(string: string|list(string)|int))'
        :type file_tree_node='dict(string: string|list(string)|int)'
        :type path='string'
        :type largest_size='int,>=0'
        :type total_size='int,>=0'
        :type depth='int,>=0'
        :rtype: 'None'
    """
    percentage = int(file_tree_node['size'] / float(total_size) * 100)

    if percentage < ARGS.hide:
        return

    print('{:>{}s} {:>4d}%  '.format(file_tree_node['print_size'],
                                     largest_size, percentage), end='')
    if ARGS.tree_view:
        print('{}{}'.format('   '*depth, os.path.basename(path)))
    else:
        print(path)

    if len(file_tree_node['children']) != 0:
        for child in file_tree_node['children']:
            print_tree(file_tree, file_tree[child], child, largest_size,
                       total_size, depth + 1)

@contract
def show_space_list(directory='.', depth=-1, order=True):
    """ Function description.
        :type directory='string'
        :type depth='int'
        :type order='boolean'
        :rtype: 'None'
    """
    abs_directory = os.path.abspath(directory)

    cmd = 'du '
    if depth != -1:
        cmd += '-d {} '.format(depth)

    cmd += abs_directory
    raw_output = subprocess_check_output(cmd)

    total_size = -1
    line_regex = r'(\d+)\s+([^\s]*|\D*)'

    file_tree = {}
    for line in re.findall(line_regex, raw_output.strip(), re.MULTILINE):
        file_path = line[-1]
        dir_path = os.path.dirname(file_path)

        file_size = int(line[0])

        if file_path == abs_directory:
            total_size = file_size

            if file_path in file_tree:
                file_tree[file_path]['size'] = file_size
            else:
                file_tree[file_path] = {
                    'children': [],
                    'size': file_size,
                }

            continue

        if file_path not in file_tree:
            file_tree[file_path] = {
                'children': [],
                'size': file_size,
            }

        if dir_path not in file_tree:
            file_tree[dir_path] = {
                'children': [],
                'size': 0,
            }

        file_tree[dir_path]['children'].append(file_path)
        file_tree[file_path]['size'] = file_size

    largest_size = 0
    for file_path in file_tree:
        file_tree_entry = file_tree[file_path]
        file_tree_entry['children'] = sorted(
            file_tree_entry['children'],
            key=lambda v: file_tree[v]['size'],
            reverse=order
        )

        file_tree_entry['print_size'] = bytes_to_readable(
            file_tree_entry['size']
        )
        largest_size = max(largest_size, len(file_tree_entry['print_size']))

    print(' ' * max(0, largest_size - len('Size')) + 'Size   (%)  File')
    print_tree(file_tree, file_tree[abs_directory], abs_directory,
               largest_size, total_size)

@contract
def main():
    """ Function description.
        :rtype: 'None'
    """
    if not ARGS.all:
        show_space_list(ARGS.directory, ARGS.depth,
                        order=(ARGS.order == 'desc'))
    else:
        show_space_list(ARGS.directory, order=(ARGS.order == 'desc'))

if __name__ == '__main__':
    main()
