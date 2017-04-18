#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
Read ps.log file and assign to each processor a corresponding NUMA node.

Read aggregation of CPUs from output of lscpu command.


Copyright 2017, Jarmila Hladká

License:
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from sys import stdin, stdout, stderr, exit


def get_input():
    """
    Parse and validate input line.
    """

    from argparse import ArgumentParser
    import os

    # Parse input line:
    usage = """

./ps2node.py --lscpu lscpu.txt < ps.log
or
ps -L -o pid, lwp, psr, comm -p ${PID} | ./ps2node.py --lscpu <(lscpu)

To process many files and replace original files:

for file in $(find ./ -name "*ps.log") ; do
  temp_file=$(mktemp)
  ./ps2node.py --lscpu lscpu.txt <"${file}" >"${temp}"
  if [[ $? == 0 ]] && [[ -s "${temp_file}" ]] ; then
    mv "${temp_file}" "${file}"
  else
    echo "ps2node.py has failed for file \"${file}\"" 1>&2
    rm "${temp_file}"
  fi
done

"""

    description = """Converts output of ps -L -o pid, lwp, psr, comm -p
        by assigning NUMA node for processors."""

    parser = ArgumentParser(description=description, usage=usage)
    parser.add_argument("--lscpu", help="Path to lscpu file.", required=True)
    args = parser.parse_args()

    # Return lscpu file:
    if args.lscpu:
        # Check if the file/link/pipe is readable:
        if os.access(args.lscpu, os.R_OK):
            return args.lscpu
        else:
            stderr.write("File {0} doesn't exist!\n".format(args.lscpu))
            exit(1)

    # If lscpu file isn't specified:
    else:
        stderr.write("Specify path to lscpu file using '--lscpu' option!\n")
        exit(1)


def CPU_NUMA(lscpu):
    """
    Make a dictionary of CPU's association with NUMA nodes.
    """

    with open(lscpu) as lscpufile:

        cpu_numa = {}

        for line in lscpufile:

            # Find number of CPUs and NUMA nodes:
            if line[:7] == 'CPU(s):':
                cpu_nb = int(line[7:])
            if line[:13] == 'NUMA node(s):':
                nodes_nb = int(line[13:])

            # Find NUMA nodes associated with CPUs:
            if line[:9] == 'NUMA node':
                words = line.split()
                cpus = words[-1].split(',')
                for cpu in cpus:
                    if '-' in cpu:
                        w = cpu.split('-')
                        for i in range(int(w[0]), int(w[1]) + 1):
                            cpu_numa[str(i)] = words[1][-1:]
                    else:
                        cpu_numa[cpu] = words[1][-1:]

        # Check if all CPUs are associated with NUMA node:
        if len(cpu_numa) != cpu_nb:
            stderr.write("CPU {0} from ps file is not associated with any NUMA \
node in lscpu file. Please check if ps file and lscpu file are from \
the same server.\n".format(cpu_nb))
            exit(1)

    return cpu_numa


def modify_ps_output(cpu_numa):
    """
    Read ps output from stdin and add corresponding NUMA nodes.
    """

    # Print first line if it's a line with date and time info:
    LINE_NUMBER = 1
    line = stdin.readline()
    if len(line.split()) == 1:
        stdout.write(line)
        line = stdin.readline()
        LINE_NUMBER += 1

    # Loop over time reports.
    while True:

        # Read and print second line with date and time info,
        # and find out in which column is processor number:
        LINE_NUMBER += 1
        columns = line.split()
        PROCESSOR_COLUMN = columns.index('PSR')
        NUMBER_OF_COLUMNS = len(columns)
        stdout.write("{0} {1}\n".format(line[:-1], 'NUMA'))

        # To control end of file:
        status = 1

        while 1:

            # Read data line:
            line = stdin.readline()
            LINE_NUMBER += 1

            columns = line.split()      # number of columns in line
            line_length = len(columns)
            # Check if there is correct number of columns with data:
            if line_length < NUMBER_OF_COLUMNS:

                # Check if it's line with date and time:
                if line_length == 1:
                    stdout.write(line)
                    line = stdin.readline()
                    columns = line.split()
                # Check if end of file:
                elif line_length == 0:
                    status = 'EOF'
                # Unexpected number of columns:
                else:
                    stderr.write("\nUnexpected data format at line {0}.\nPlease check ps output.\n".format(LINE_NUMBER))
                    exit(1)
                break

            # Check if there is a number in PSR column:
            try:
                processor = columns[PROCESSOR_COLUMN]
                int(processor)
            except ValueError:
                break

            # Look in dictionary and find corresponding number of NUMA node:
            # Name of command can contain whitespace:
            numa_node = cpu_numa[processor]
            stdout.write("{0} {1}\n".format(line[:-1], numa_node))

        # Check for end of file:
        if len(columns) == 0:
            exit(0)

        # write a line with date and time if no end of file:
        if status == 'EOF':
            break


if __name__ == "__main__":

    cpu_numa = CPU_NUMA(get_input())
    modify_ps_output(cpu_numa)
