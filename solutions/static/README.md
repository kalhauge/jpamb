# Modular static analysis: signs, intervals, strings, and array execution

This solution keeps JPAMB's existing worklist, instruction matching, entry points,
and prediction protocol. All implementation changes are under `solutions/static`;
the JPAMB library, CLI, decoder, and Java benchmark sources are unchanged.

## Setup (WSL / Bash)

From this checkout:

```bash
cd /home/sweet/project_PA/pa-code
source .venv/bin/activate
```

On a fresh checkout, install the projects and test dependencies first:

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e . -e solutions/static pytest hypothesis
```

## Select abstractions independently or together

```bash
# Individual domains
jpamb analyse -- static-analysis --abstractions sign
jpamb analyse -- static-analysis --abstractions interval
jpamb analyse -- static-analysis --abstractions string

# Pairs
jpamb analyse -- static-analysis --abstractions sign,interval
jpamb analyse -- static-analysis --abstractions sign,string
jpamb analyse -- static-analysis --abstractions interval,string

# All three
jpamb analyse -- static-analysis --abstractions sign,interval,string
```

Sign analysis remains the default if `--abstractions` is omitted. Order does not
matter: `string,interval,sign` selects the same domains as `sign,interval,string`.
Unknown or empty names produce a CLI error. The `info` tags list selected domains.

| Selection | Integer / boolean representation | String contents |
| --- | --- | --- |
| `sign` | SignSet | Unsupported |
| `interval` | Interval | Unsupported |
| `string` | BooleanSet only | StringSet |
| `sign,interval` | SignInterval | Unsupported |
| `sign,string` | SignSet | StringSet |
| `interval,string` | Interval | StringSet |
| `sign,interval,string` | SignInterval | StringSet |

String-only mode never uses SignSet or Interval. Its BooleanSet handles true,
false, or both, including JVM constants 0 and 1. General integer parameters,
arithmetic, increments, negation, and other integer constants are unsupported.
Trivial methods using only 0/1 and branching can still execute because JVM
booleans use integer bytecodes.

Put JPAMB options before `--` and analyzer options after the executable name.
Do not quote the entire analyzer command as one argument:

```bash
jpamb analyse --filter Simple --iterations 1 -- static-analysis --abstractions interval
jpamb analyse --filter Strings --iterations 1 -- static-analysis --abstractions interval,string

static-analysis --help
static-analysis --abstractions sign,interval,string info
static-analysis --abstractions interval 'jpamb.cases.Simple.divideByN:(I)I'
```

## Separate interpreter runs and reports

```bash
# Integer examples
jpamb interpret --abstract --filter Simple -- static-interpreter --abstractions sign
jpamb interpret --abstract --filter Simple -- static-interpreter --abstractions interval
jpamb interpret --abstract --filter Simple -- static-interpreter --abstractions sign,interval

# String examples in each supporting configuration
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions string
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions sign,string
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions interval,string
jpamb interpret --abstract --filter Strings -- static-interpreter --abstractions sign,interval,string

# One concrete execution trace
static-interpreter --abstractions interval 'jpamb.cases.Simple.divideByN:(I)I' '(2)' 100
```

Remove the filter to exercise the full suite; unsupported cases are still expected.
To save independent analysis reports for all configurations:

```bash
mkdir -p reports
for domains in sign interval string sign,interval sign,string interval,string sign,interval,string; do
    jpamb analyse --report "reports/${domains}-analysis.sexp" -- static-analysis --abstractions "$domains"
done
```

JPAMB requires three iterations for saved analysis reports (the default). Do not
combine `--report` with `--filter`. The `reports/` directory is ignored by Git.

Separate commands produce separate analyses. A comma-separated selection makes
the domains cooperate inside ONE analysis; it does not merge independent reports.
Scores on the current suite are compatibility observations, not the goal of these
changes. Dedicated accuracy tests should check both coverage of real outcomes and
unnecessary extra predictions. Only one existing benchmark uses Java String.

## Array support and score checks

Array instructions work automatically whenever an integer domain is selected;
there is no extra `array` abstraction option. Supported arrays are one-dimensional
`int[]` and `char[]`. String-only mode deliberately does not enable integer array
analysis. Integer modes with string support can use both types of heap objects.

To evaluate analysis scores, run from the repository root in the active venv:

```bash
# Full-suite scores, with JPAMB's default three iterations.
jpamb analyse -- static-analysis --abstractions sign
jpamb analyse -- static-analysis --abstractions interval
jpamb analyse -- static-analysis --abstractions sign,interval,string

# Quick array-only score check (one iteration, no saved report).
jpamb analyse --filter Arrays --iterations 1 -- static-analysis --abstractions interval

# Validate concrete array cases and the unknown-input cases.
jpamb interpret --abstract --max-steps 300 --filter Arrays -- static-interpreter --abstractions interval
jpamb interpret --abstract --max-steps 300 --filter Arrays -- static-interpreter --abstractions sign,interval
```

Use `--max-steps 300` for array interpreter validation. At JPAMB's default
100-step budget, some loop-heavy cases exhaust the trace budget before covering
all required program points (28/30 with signs, 25/30 with interval modes in the
validation run). At 300 steps, all three integer configurations pass 30/30.
The interpreter's default budget and scheduling policy have not been changed.

## Implementation information

The detailed explanations have moved to [information/static_analysis.md](../../information/static_analysis.md).
It covers intervals, combined signs and intervals, strings, array summaries,
widening, the code map, and current limitations.

See [information/score_similarity.md](../../information/score_similarity.md) for
why some configurations score alike and example methods that can reveal their
differences. Setup, execution commands, and test instructions remain here.

## Branch refinement

All domain selections now refine branch operands, including stored locals,
null checks, and `String.equals` predicates. See
[branch refinement and results](../../information/branch_refinement.md) for the
implementation, limitations, paired score table, and interpreter validation.

Reproduce the seven-configuration comparison against the array-support baseline:

```bash
python solutions/static/scripts/compare_branch_refinement.py
```

## Tests

```bash
python -m pytest solutions/static/tests -q
```

Interval tests cover lattice properties, concrete Java arithmetic and comparisons,
integer boundaries, zero divisors, remainder, normalization, nonzero combined
ranges, widening convergence, branch joins, bounded assertions, CLI metadata,
trace serialization, and cooperation with string execution. Previously skipped
interval tests are now enabled. Existing sign and string tests remain, including
tests that forbid SignSet use in string-only mode.


Array tests additionally cover allocation defaults, empty arrays, negative and
uncertain indices, null access, weak stores and aliases, parameter abstraction,
UTF-16 char stores, mixed heap joins, heap widening, stack duplication, CLI
predictions, and string-only isolation. Earlier tests expecting arrays to be
unsupported now use unsupported general method calls instead.

Array-support validation: 175 static tests passed; sign, interval, and combined
sign-interval modes passed 30/30 array interpreter cases at a 300-step budget.
Full-suite three-iteration reports were generated for all seven selections.
In this run the scores were 146.20 (sign), 156.15 (interval or sign+interval),
148.74 (sign+string), 158.62 (interval+string or all three), and 72.90 (string).
Scores describe this benchmark version, not general proof of soundness or accuracy.
