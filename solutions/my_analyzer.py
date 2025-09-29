#!/usr/bin/env python3
import sys
import re
import jpamb



# this example shows minimal working program without any imports.
#  this is especially useful for people building it in other programming languages
if len(sys.argv) == 2 and sys.argv[1] == "info":
    # Output the 5 required info lines
    print("My First Analyzer")
    print("1.0")
    print("Student Group Name")
    print("simple,python")
    print("no")  # Use any other string to share system info
else:
    # Get the method we need to analyze
    classname, methodname, args = re.match(r"(.*)\.(.*):(.*)", sys.argv[1]).groups()

    # Make predictions (improve these by looking at the Java code!)
    ok_chance = "90%"
    divide_by_zero_chance = "10%"
    assertion_error_chance = "5%"
    out_of_bounds_chance = "0%"
    null_pointer_chance = "0%"
    infinite_loop_chance = "0%"

    # Output predictions for all 6 possible outcomes
    print(f"ok;{ok_chance}")
    print(f"divide by zero;{divide_by_zero_chance}")
    print(f"assertion error;{assertion_error_chance}")
    print(f"out of bounds;{out_of_bounds_chance}")
    print(f"null pointer;{null_pointer_chance}")
    print(f"*;{infinite_loop_chance}")
