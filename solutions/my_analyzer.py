#!/usr/bin/env python3
import sys
import re
from interpreter import *
import jpamb
import random
from loguru import logger

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
    java_max_int = 2**32-1
    java_min_int = -2**32

    # Make predictions (improve these by looking at the Java code!)
    ok_chance = "50%"
    divide_by_zero_chance = "50%"
    assertion_error_chance = "50%"
    out_of_bounds_chance = "50%"
    null_pointer_chance = "50%"
    infinite_loop_chance = "50%"

    methodid = jpamb.parse_methodid(sys.argv[1])
    states = set()
    fuzzing_tests = 100

    if args.startswith("()"):
        input = jpamb.parse_input("()")
        state = execute(methodid, input)
        states.add(state)
    else:
        arg_types = list(args)[1:-2]
        for _ in range(fuzzing_tests):
            arg_values = []
            for a in arg_types:
                match a:
                    case "I":
                        arg_values.append(str(random.randint(java_min_int, java_max_int)))
                    case "Z":
                        arg_values.append(random.choice(["true", "false"]))
                    case _:
                        raise NotImplementedError(f"Don't know how to handle argument type {a}")
                    
            input = jpamb.parse_input(f"({",".join(arg_values)})")
            state = execute(methodid, input)
            states.add(state)
    

    # if no args then outcome=0 => chance=0
    if "assertion error" in states:
        assertion_error_chance = "100%"
    else:
        assertion_error_chance = "15%"

    if "ok" in states:
        ok_chance = "100%" 
    else:
        ok_chance = "15%"

    if "divide by zero" in states:
        divide_by_zero_chance = "100%" 
    else:
        divide_by_zero_chance = "15%"

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
