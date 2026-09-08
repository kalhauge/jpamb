#!/usr/bin/env python3
import re
import sys


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "info":
        print("My First Analyzer")
        print("1.0")
        print("Student Group Name")
        print("simple,python")
        print("no")  # Use any other string to share system info
    else:
        _classname, _methodname, _args = re.match(
            r"(.*)\.(.*):(.*)", sys.argv[1]
        ).groups()

        ok_chance = "yes"
        divide_by_zero_chance = "no"
        assertion_error_chance = "50%"
        out_of_bounds_chance = "-1.23"
        null_pointer_chance = "maybe"
        infinite_loop_chance = "yes"

        print(f"ok;{ok_chance}")
        print(f"divide by zero;{divide_by_zero_chance}")
        print(f"assertion error;{assertion_error_chance}")
        print(f"out of bounds;{out_of_bounds_chance}")
        print(f"null pointer;{null_pointer_chance}")
        print(f"*;{infinite_loop_chance}")
