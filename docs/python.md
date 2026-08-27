# Python

Can't live with it, can't live without it.

## Running Python Applications

To run Python applications, we recommend creating a virtual environment containing
both your Python applications dependencies and JPAMB.

```bash
$ uv venv --no-project --clear --prompt jpamb-eval .jpamb-eval
```

Now activate the virtual environment:

```bash
# Using bash (but look for other options) 
$ source .jpamb-eval/bin/activate
```

After this you should see a `(jpamb-eval)` in your prompt.

Now you can install both JPAMB and your python project in this new environment.
For example to run any of the solution in [](solution/), you can do the following:

```bash
$ uv pip install --editable . # Installs JPAMB
$ uv pip install --editable solutions/* # Installs all solutions
```

Now you should be able to run JPAMB on any of the installed programs:

```bash
$ jpamb -v analyse syntatic-bytecode
```

## Library

When writing Python applications you can include the `JPAMB` as a dependency.

Currently there is no documentation for these methods, but you can look up
the source code at [](src/jpamb.py) and [](src/jvm).

### Automatic script setup with `getmethodid` and `getcase`

Two useful utility methods are the `getmethodid` and `getcase` method, which prints the correct
stats and parses the method and (potential inputs for you:

```python
import jpamb

def analysis():
    methodid = jpamb.getmethodid(
        "apriori",
        "1.0",
        "The Rice Theorem Cookers",
        ["cheat", "python", "stats"],
        for_science=True,
    )
    # methodid is of type `jpamb.jvm.AbsMethodID`

    # ... rest of the analysis
```

or

```python
import jpamb

def interpreter()
    methodid, input = jpamb.getcase(
        "apriori",
        "1.0",
        "The Rice Theorem Cookers",
        ["cheat", "python", "stats"],
        for_science=True,
    )
    # methodid is of type `jpamb.jvm.AbsMethodID`
    # input is of type `jpamb.Input.

    # ... rest of the interpreter
```
