# JPAMB: Java Program Analysis Micro Benchmarks

## What is this?

JPAMB is a collection of small Java programs with various behaviors (crashes, infinite loops, normal completion). Your task is to build a program analysis tool that can predict what will happen when these programs run.

Think of it like a fortune teller for code: given a Java method, can your analysis predict if it will crash, run forever, or complete successfully?

## Quick Links

- **[uv documentation](https://docs.astral.sh/uv/)** - Python package manager we use
- **[Tree-sitter Java](https://tree-sitter.github.io/tree-sitter/using-parsers)** - For parsing Java source code
- **[JVM2JSON codec](https://github.com/kalhauge/jvm2json/blob/main/CODEC.txt)** - Understanding bytecode format
- **[Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)** - Windows C++ compiler
- **[JPAMB GitHub Issues](https://github.com/kalhauge/jpamb/issues)** - Get help if stuck

## Setup

### Step 0: Get familiar with your shell

If you do not already know how your shell works, consider looking at the first couple of
lectures of the [MIT Missing Semester](https://missing.csail.mit.edu/).

### Step 1: Install GCC (required for compilation)

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install build-essential
```

**Windows:**

```bash
# Install Microsoft Visual C++ 14.0 (required for Python C extensions)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Or install via Visual Studio Installer and select "C++ build tools"

# Alternative: Install Visual Studio Community (includes build tools)
winget install Microsoft.VisualStudio.2022.Community
```

**Mac:**

```bash
# Install Xcode command line tools
xcode-select --install
```

### Step 2: Install uv (Python package manager)

```bash
# On Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Important:** Restart your terminal/command prompt after installing uv!

### Step 3: Verify everything works

*Note: It is **no longer recommended** that you install the tool with `uv tool install`.*

```bash
uv run jpamb checkhealth
```

You should see several green "ok" messages. If you see any red errors, check troubleshooting below!

## How It Works

### Your Task

Build a program that analyzes Java methods and predicts what will happen when they run.

### Your Program Must Support Two Commands:

Here we use `./your_analyzer` to be name of the program you are going to
write.

**1. Info command** - tells us about your analyzer:

```bash
./your_analyzer info
```

This should output 5 lines:

- Your analyzer's name
- Version number
- Your team/group name
- Tags describing your approach (e.g., "static,dataflow")
- Either your system info (to help us improve and for science) or "no" (for privacy)

**2. Analysis command** - makes predictions:

```bash
./your_analyzer "jpamb.cases.Simple.divideByZero:()I"
```

Given the encoded name of a method (see [`cases.txt`](target/stats/cases.txt) for a full list of examples), this should output 0 or more lines containing predictions, which you can read about in the next section.

**Assumptions**

You can rely on the following assumptions:

1. Your program will always run in the JPAMB folder. This means that you can access files like `src/main/java/jpamb/cases/Simple.java` from your program.

1. All methods presented to the analysis comes from files in the `src/main/java/jpamb/cases/` folder, and can be uniquely identified by their method name.

1. Only the stdout is captured by JPAMB, so you can output debug information in the stderr.

### What Can Happen to Java Methods?

Your analyzer need to predict if there exist an input to the method where
one of these possible outcomes can happen:

| Outcome | What it means |
|---------|---------------|
| `ok` | Method runs and finishes normally |
| `divide by zero` | Method tries to divide by zero |
| `assertion error` | Method fails an assertion (like `assert x > 0`) |
| `out of bounds` | Method accesses array outside its bounds |
| `null pointer` | Method tries to use a null reference |
| `*` | Method runs forever (infinite loop) |

### Making Predictions

For each outcome, you give either:

- **A percentage**: `75%` means "75% of all methods that looks like this will have this outcome"
- **A wager**: `5` means "bet 5 points this will happen", `-10` means "bet 10 points this WON'T happen"

**Example output:**

```
ok;80%
divide by zero;20%
assertion error;0%
out of bounds;5
null pointer;0%
*;0%
```

## Your First Analyzer

### Step 1: Look at example Java code

Check out the test cases in `src/main/java/jpamb/cases/Simple.java` - these are
(some of) the methods your analyzer will predict the behavior of.

For example, `assertBoolean` has two known outcomes. If given `false` it throws
an `assertion error`, and if given `true` it finishes normally `ok`.

```java
@Case("(false) -> assertion error")
@Case("(true) -> ok")
public static void assertBoolean(boolean shouldFail) {
    assert shouldFail;
}
```

### Step 2: Create your first analyzer

Create a file called `my_analyzer.py` in the root directory. If you place it somewhere
else replace `my_analyzer.py` with the path to your script or executable:

```python
import sys
import re

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
```

### Step 3: Run your analyzer

First, make sure that your script runs outside the JPAMB framework. If you
have python installed on your system you can run:

```bash
python ./my_analyzer.py info
```

But, you can also run it with the same interpreter as the JPAMB framework,
like so:

```bash
uv run ./my_analyzer.py info
```

This command should output the data from above.
You should also be able to run it with a method name like `jpamb.cases.Simple.divideByZero:()I`.

### Step 4: Test your analyzer

Now you should be able to test the analyser.
In the begining we recommend adding the `--filter "Simple"`, which
focuses you on the methods from the `src/main/java/jpamb/cases/Simple.java`
file:

```bash
# Test on just the Simple cases to start
# Linux/Mac/Windows (all the same):
uv run jpamb test --filter "Simple" <your-intepreter> my_analyzer.py
```

You should see output showing scores for each test case. Don't worry about the scores yet - focus on getting it working!

Also if you are using python, you can use the `--with-python` flag, which
runs the analyser with the same interpreter as JPAMB.

```bash
uv run jpamb test --filter "Simple" --with-python my_analyzer.py
```

### Step 5: Improve your analyzer

*Mini Task:* To improve your analyser you first have to find the class
and then the method in that class. In Java, classes are always placed
after their classnames, so you can find `jpamb.cases.Simple` in the source file `src/main/java/jpamb/cases/Simple.java`.

*Tip* you might use a regular expression to find the content of a method.
[`r"assertFalse.*{([^}]*)}"`](https://regex101.com/r/jDSC6S/1) and pythons
[re](https://docs.python.org/3/library/re.html#re.Match) library.

Now look at the Java code and try to make better predictions. For example:

- If you see `1/0` in the code, predict `divide by zero;100%`
- If you see `assert false`, predict `assertion error;100%`
- If you see `while(true)`, predict `*;100%` (infinite loop)

A useful tool for seeing where you can improve your analyzer is by using the plot command.

```bash
uv run jpamb plot --report <your-report.json> 
```

This will plot the score achieved and the relative time used on analyzing every test case.

If you have multiple reports you want to compare this can be done by using

```bash
uv run jpamb plot --directory <your-report-directory> 
```

This will scan the given directory for json files, and make a comparative plot.

## Using the JPAMB library

When writing more complex analysed you might want to make use of the jpamb
library, especially, the modules `jpamb/__init__.py`, `jpamb/model.py`, and in `jpamb/jvm/`. To use
this library, do this you have include `jpamb` in your interpreter. The easiest
way to do that its just to use the interpreter used by `jpamb`. In the `jpamb`
directory you can do this by the command `uv run`:

```bash
uv run ./my_analysis.py info
```

### Automatic script setup with `getmethodid`

One useful utility method is the `getmethodid` method, which prints the correct
stats and parses the method for you:

```python
import jpamb

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

### Source file lookup with `sourcefile`

You can use the `sourcefile` method to get the source file of
the corresponding method or class.

```python
src = jpamb.sourcefile(methodid)

txt = open(src).read()
```

## Scoring (Advanced)

**For most assignments, you can ignore this section and just use percentages!**

Instead of percentages, you can use **wagers** (betting points):

- Positive wager (e.g., `divide by zero;5`) means "I bet 5 points this WILL happen"
- Negative wager (e.g., `divide by zero;-10`) means "I bet 10 points this WON'T happen"
- Higher wagers = higher risk/reward

The scoring formula: `points = 1 - 1/(wager + 1)` if you win, `-wager` if you lose.

## Testing Your Analyzer

You can test your analyser using the different command line tools.
Here `-W` is used to tell `jpamb` that the executable is a python file
and should be run with the same interpreter as `jpamb`.

```bash
# Test on simple cases first
uv run jpamb test --filter "Simple" -W my_analyzer.py

# Test on all cases  
uv run jpamb test -W my_analyzer.py

# Generate final evaluation report
uv run jpamb evaluate -W my_analyzer.py > my_results.json
```

## Advanced: Analyzing Approaches

### Source Code Analysis

- Java source code is in `src/main/java/jpamb/cases/`
- Example: `solutions/syntaxer.py` uses tree-sitter to parse Java

### Bytecode Analysis

- Pre-decompiled JVM bytecode in `target/decompiled/` directory
- Example: `solutions/bytecoder.py` analyzes JVM opcodes
- Python interface: `lib/jpamb/jvm/opcode.py`

### Statistics or Cheat-Based

- Historical data in `target/stats/distribution.csv`
- Example: `solutions/apriori.py` uses statistical patterns

## Troubleshooting

**"Command not found" errors:**

- Make sure you restart your terminal after installing uv
- Try `which uv` to see if it's installed correctly

**"Health check fails":**

- Make sure you're in the jpamb directory
- Make sure GCC is installed (Step 1 above)
- Try `mvn compile` to build the Java code first

**"Permission denied" when running analyzer:**

- Linux/Mac: Use `chmod +x my_analyzer.py` to make it executable
- All platforms: Use `python my_analyzer.py` instead of `./my_analyzer.py`

**Windows users:**

- Use PowerShell or Command Prompt
- Replace `/` with `\` in file paths if needed
- Consider using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) for easier setup

**Still stuck?** Check the example solutions in `solutions/` directory or ask for help!

## Adding Your Own Cases

To get started with adding your own cases, please make sure to download
either `docker` or `podman` (recommended).

You can add your own cases to the benchmark suite by adding
them in the source folder:

```
src/main/java/jpamb/cases
    ├── Arrays.java
    ├── Calls.java
    ├── Loops.java
    ├── Simple.java
    └── Tricky.java
```

and then running the following command:

```
$ uv run jpamb build
```

This will download a docker container and run the build in that. This ensures
consistent builds across systems.

**Warning:** If you create new folders and use docker, it might create them as root. To fix
this either use podman or change the permissions after.
