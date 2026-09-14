
import jpamb


def main():
    methodid = jpamb.getmethodid(
        name="My First Analyzer",
        version="1.0",
        group="Student Group Name",
        tags=["simple", "python"],
        for_science=True,
    )

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
