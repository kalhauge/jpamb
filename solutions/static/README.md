# Static analysis: signs and strings

This solution keeps JPAMB's existing worklist, instruction matching, state joins,
entry points, and prediction protocol. No changes to the JPAMB library or CLI are
needed. All implementation changes live under `solutions/static`.

## Setup (WSL / Bash)

Run from this checkout, not another JPAMB checkout:

```bash
cd /home/sweet/project_PA/pa-code
source .venv/bin/activate
```

The local `.venv` was created for this implementation. On a fresh checkout:

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e . -e solutions/static pytest hypothesis
```

## Select abstractions on the command line

```bash
# Original sign analysis (also the default when the option is omitted).
jpamb analyse -- static-analysis --abstractions sign

# Strings cooperating with signs in one analysis.
jpamb analyse -- static-analysis --abstractions sign,string

# Strings only, with minimal boolean support and no sign analysis.
jpamb analyse -- static-analysis --abstractions string
```

Put JPAMB options before `--`, and analyzer options after the program name:

```bash
jpamb analyse --filter Strings --iterations 1 -- static-analysis --abstractions sign,string
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions sign,string
```

`--` stops JPAMB from trying to parse the analyzer's options. Do not quote the
whole analyzer command as one argument. Options also work with direct calls:

```bash
static-analysis --help
static-analysis --abstractions sign,string info
static-analysis --abstractions sign,string 'jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V'
static-interpreter --abstractions sign,string 'jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V' "(s'hello')" 100
```

Available selections:

| Selection | Integer / boolean values | String contents |
| --- | --- | --- |
| `sign` (default) | SignSet | Unsupported |
| `string` | BooleanSet only (no general integer analysis) | StringSet |
| `sign,string` | SignSet | StringSet |

`string` does not use SignSet. It uses a small `BooleanSet` to represent false,
true, or both, including JVM boolean constants 0 and 1. This supports string
comparison results, assertion checks, boolean parameters, and branching.
General integer parameters, other integer constants, arithmetic, increments,
and negation are unsupported and cause incomplete/`unknown` analysis.
Since JVM boolean constants are integer bytecodes, trivial methods involving
only 0/1 and branches can still run; this does not enable general integer analysis.
Selected domains appear in JPAMB's `info` tags. Unknown names, including the
unfinished `interval` domain, are rejected with an explanatory CLI error.

To compare configurations separately, run the three analysis commands above.
They keep separate states and reports. `sign,string` means cooperation inside
one run; it does not run two analyzers and merge their predictions. There is no
sign/interval product domain or automatic multi-run report merger yet.

## Run and save each configuration separately

Run these commands from the repository root with the virtual environment active:

```bash
mkdir -p reports

# Separate analysis reports. JPAMB defaults to the required three iterations.
jpamb analyse --report reports/sign-analysis.sexp -- static-analysis --abstractions sign
jpamb analyse --report reports/string-analysis.sexp -- static-analysis --abstractions string
jpamb analyse --report reports/sign-string-analysis.sexp -- static-analysis --abstractions sign,string

# Separate abstract-interpreter runs.
jpamb interpret --abstract -- static-interpreter --abstractions sign
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions string
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions sign,string
```

Do not combine `--report` with `--filter`, or use one iteration for a saved
analysis report: JPAMB requires full-suite reports with three iterations.
The `reports/` directory is ignored by Git. Remove `--filter Strings` to exercise
string-enabled interpreter configurations against the full suite; unsupported
cases are expected, particularly in string-only mode.

The current suite has only one Java String benchmark method. Treat its overall
score as a compatibility check, not a measure of string-analysis quality. Future
dedicated string cases should check outcome coverage and precision in each mode.

## Changes in this branch

- Added `IntegerAbstraction`, bounded `StringSet`, and independent `BooleanSet`.
- Added `--abstractions sign`, `string`, and `sign,string` selection and metadata.
- Generalized interpreter values and added references and a copy-on-update heap.
- Added string inputs/constants, reference operations, and `String.equals`.
- Kept unsupported operations explicit and retained JPAMB's existing execution
  and reporting structure. The JPAMB core and benchmark sources are unchanged.
- Added domain, execution, CLI, serialization, and string-only isolation tests.

## How the implementation works

1. `configuration.py` consumes `--abstractions` and leaves the original JPAMB
   positional arguments (`info`, method, input, step limit) for JPAMB to parse.
2. `IntegerAbstraction` in `abstractions.py` specifies the existing integer
   operations. `SignSet` implements it; the interpreter constructs integer values
   through `AnalysisConfig.scalar` rather than naming `SignSet`. With string-only
   selection, `integer_domain` is `None` and `scalar` creates `BooleanSet` values.
   Arithmetic handlers explicitly require an enabled integer domain.
3. `StringSet` holds up to eight exact strings. An empty set is bottom; `None` is
   top (any contents). Joining more than eight strings produces top. The empty
   string is an ordinary concrete value and is different from bottom.
4. Locals and the operand stack hold integer values, boolean values, or references.
   `None` in a local means uninitialized, not Java null. The heap maps stable
   parameter/literal IDs to string contents. Successors copy the heap on updates;
   state joins combine reference targets and heap contents.
5. `string_methods.py` models `String.equals(Object)`. It compares every possible
   pair of contents and returns possible boolean answers and null-pointer errors.
   The interpreter converts answers to `BooleanSet` in string-only mode, or through
   the chosen integer domain in combined mode, then uses the existing branches.

For example, `{"hello", "bye"}.equals({"hello"})` produces both true and false.
With signs those results become `{0,+}`; with string-only mode they remain
`{false,true}`. In both modes the existing interpreter follows
both assertion outcomes. Java reference equality is handled separately from
content equality. Parameter objects may alias; matching summary locations do
not prove identity. Literal locations use Java's string interning semantics.

Supplied string inputs are non-null exact contents. Unknown string parameters
include both arbitrary contents and null. Therefore analysis of `sayHello` reports
possible normal completion, assertion failure, and null-pointer error. The last
possibility is conservative even though the current benchmark annotations only
list non-null examples. Normal successors are emitted only if a call has a
possible normal result.

## Adding an integer abstraction later

1. Finish `Interval` in `abstractions.py` and make it implement
   `IntegerAbstraction`: abstraction, top/bottom, ordering, join/meet, membership,
   arithmetic, comparisons, and trace serialization.
2. Account for Java 32-bit arithmetic and establish a practical loop-convergence
   policy (for example, widening) before enabling it.
3. Add its name to `parse_options` and map the selection to
   `AnalysisConfig(integer_domain=Interval, strings=...)`. Update the metadata
   tags there to reflect the chosen integer domain; currently `sign` is included
   only when sign analysis is selected.
4. Define `interval,string` as interval integers plus the existing string support.
   Reject `sign,interval` until a genuine product domain or explicit independent
   run mode is implemented; do not silently choose one.
5. Add domain and integration tests. The worklist and string equality handler
   should not need to be copied or rewritten.

## Current scope and limitations

Supported additions: string parameters/constants, reference load/store, null
constants, reference comparisons using the existing decoded comparison operators,
and the exact `java.lang.String.equals(Object)` method signature. JVM decoding is
unchanged; unsupported instruction encodings still fail explicitly.

Length, concatenation, substring, constructors, arbitrary object arguments,
arrays, general method execution, and exception handlers are not added here.
Unknown calls mark analysis incomplete, preserving `unknown` predictions.
The original assertion-allocation shortcut, 300-step analysis budget, lack of
branch refinement, and `unknown` nontermination prediction remain in place.

## Tests

```bash
python -m pytest solutions/static/tests -q
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions sign,string
```

Tests cover bounded-set lattice laws and concrete equality containment, null and
identity semantics, heap joins, options/metadata, unsupported selections and
calls, both concrete string benchmark inputs, unknown input, and trace parsing.
Tests also prevent any SignSet use in string-only execution and check that
integer operations are rejected in that mode. The existing integer regression
tests run unchanged. Existing interval tests stay skipped until interval
implementation is undertaken.

Validation for this change: 57 static tests passed, 3 existing interval tests
skipped; both string-enabled interpreter modes passed all 3 String cases.
