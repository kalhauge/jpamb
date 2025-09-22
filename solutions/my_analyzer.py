#!/usr/bin/env python3
import sys
import re
from interpreter import *
import jpamb

# this example shows minimal working program without any imports.
#  this is especially useful for people building it in other programming languages
if len(sys.argv) == 2 and sys.argv[1] == "info":
    # Output the 5 required info lines
    print("Dynamic Analysis")
    print("1.0")
    print("Kageklubben")
    print("simple,python,dynamic")
    print("no")  # Use any other string to share system info
else:
    # Get the method we need to analyze
    classname, methodname, args = re.match(r"(.*)\.(.*):(.*)", sys.argv[1]).groups()

    # Make predictions (improve these by looking at the Java code!)
    ok_chance = "50%"
    divide_by_zero_chance = "50%"
    assertion_error_chance = "50%"
    out_of_bounds_chance = "50%"
    null_pointer_chance = "50%"
    infinite_loop_chance = "50%"

    if args.startswith("()"):
        methodid = jpamb.parse_methodid(sys.argv[1])
        frame = Frame.from_method(methodid)
        
        state = State({}, Stack.empty().push(frame))

        for x in range(1000):
            state = step(state)
            if isinstance(state, str):
                break
        else:
            print("*")


        assertion_error_chance = "100%" if state == "assertion error" else "0%"
        ok_chance = "100%" if state == "ok" else "0%"
        divide_by_zero_chance = "100%" if state == "divide by zero" else "0%"
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
