#!/usr/bin/env python3
import sys
import re
from interpreter import *
import jpamb
import random
from loguru import logger
import tree_sitter
import tree_sitter_java

# this example shows minimal working program without any imports.
#  this is especially useful for people building it in other programming languages
if len(sys.argv) == 2 and sys.argv[1] == "info":
    # Output the 5 required info lines
    print("Dynamic Analysis")
    print("1.2")
    print("Kageklubben")
    print("simple,tricky,loops,python,dynamic")
    print("no")  # Use any other string to share system info
else:
    # Get the method we need to analyze
    classname, methodname, args = re.match(r"(.*)\.(.*):(.*)", sys.argv[1]).groups()
    java_max_int = 2**32-1
    java_min_int = -2**32

    methodid = jpamb.parse_methodid(sys.argv[1])

    int_test_vals = {"-1", "0", "1"}


    JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
    parser = tree_sitter.Parser(JAVA_LANGUAGE)


    srcfile = jpamb.sourcefile(methodid)

    with open(srcfile, "rb") as f:
        tree = parser.parse(f.read())

    simple_classname = str(methodid.classname.name)
    
    class_q = JAVA_LANGUAGE.query(
        f"""
        (class_declaration 
            name: ((identifier) @class-name 
                (#eq? @class-name "{simple_classname}"))) @class
    """
    )

    for node in tree_sitter.QueryCursor(class_q).captures(tree.root_node)["class"]:
        break
    else:
        #could not find class with name {simple_classname}
        sys.exit(-1)

    method_name = methodid.extension.name

    method_q = JAVA_LANGUAGE.query(
        f"""
        (method_declaration name: 
        ((identifier) @method-name (#eq? @method-name "{method_name}"))
        ) @method
    """
    )

    for node in tree_sitter.QueryCursor(method_q).captures(node)["method"]:
        body = node.child_by_field_name("body")
        method_body = body.text.decode()
        numbers_in_body = re.findall(r"\d+", method_body)
        for n in numbers_in_body:
            int_test_vals.add(n)
            

    # Make predictions (improve these by looking at the Java code!)
    ok_chance = "50%"
    divide_by_zero_chance = "50%"
    assertion_error_chance = "50%"
    out_of_bounds_chance = "50%"
    null_pointer_chance = "50%"
    infinite_loop_chance = "50%"
    completed_interpreter_classes = ["jpamb.cases.Simple", "jpamb.cases.Tricky", "jpamb.cases.Loops"]

    if classname in completed_interpreter_classes:

        states = set()
        int_test_vals = list(int_test_vals)
        bool_test_vals = ["true", "false"]

        fuzzing_tests = 100

        if args.startswith("()"):
            input = jpamb.parse_input("()")
            state = execute(methodid, input)
            states.add(state)
        else:
            arg_types = list(args)[1:-2]
            for index in range(len(int_test_vals)*len(bool_test_vals)):
                arg_values = []
                for a in arg_types:
                    match a:
                        case "I":
                            arg_values.append(str(int_test_vals[index % len(int_test_vals)]))
                        case "Z":
                            arg_values.append(str(bool_test_vals[index % len(bool_test_vals)]))
                        case _:
                            raise NotImplementedError(f"Don't know how to handle argument type {a}")
                        
                input = jpamb.parse_input(f"({",".join(arg_values)})")
                logger.disable("interpreter")
                state = execute(methodid, input)
                logger.enable("interpreter")
                states.add(state)

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
                logger.disable("interpreter")
                state = execute(methodid, input)
                logger.enable("interpreter")
                states.add(state)
        

        if "assertion error" in states:
            assertion_error_chance = "100%"
        else:
            assertion_error_chance = "0%"

        if "ok" in states:
            ok_chance = "100%" 
        else:
            ok_chance = "0%"

        if "divide by zero" in states:
            divide_by_zero_chance = "100%" 
        else:
            divide_by_zero_chance = "0%"
            
        if "out of bounds" in state:
            out_of_bounds_chance = "100%"
        else:
            out_of_bounds_chance = "0%"

        if "null pointer" in states: 
            null_pointer_chance = "100%"
        else:
            null_pointer_chance = "0%"

        if "*" in states:
            infinite_loop_chance = "100%"
        else:
            infinite_loop_chance = "0%"
            

    # Output predictions for all 6 possible outcomes
    print(f"ok;{ok_chance}")
    print(f"divide by zero;{divide_by_zero_chance}")
    print(f"assertion error;{assertion_error_chance}")
    print(f"out of bounds;{out_of_bounds_chance}")
    print(f"null pointer;{null_pointer_chance}")
    print(f"*;{infinite_loop_chance}")
