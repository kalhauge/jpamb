import jpamb


def main():
    _methodid, _input, _max_steps = jpamb.getcase(
        name="My First Analyzer",
        version="1.0",
        group="Student Group Name",
        tags=["simple", "python"],
        for_science=True,
    )

    print("(init ())")
    print('(step :before () :pc "cls.method:()V:0" :after "ok")')
