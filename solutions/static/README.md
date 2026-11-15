# Modular static analysis: signs, intervals, and strings

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

## How intervals work

`Interval(min, max)` represents every Java int between inclusive bounds:

- `[5, 5]`: exactly 5.
- `[2, 5]`: 2, 3, 4, or 5.
- `[-2147483648, 2147483647]`: top, any Java int.
- `[1, 0]`: bottom, no possible value. Every empty interval is normalized to this.

For branches assigning 2 and 5, the joined interval is `[2, 5]`. Adding 3 gives
`[5, 8]`. Comparing that result with 10 using `<` gives only true, because even
the maximum is below 10. Extra values in a range are allowed, but actual values
must never be omitted.

`Interval` implements the same IntegerAbstraction interface as SignSet:
abstraction, membership, containment ordering, join/meet, arithmetic, comparisons,
trace serialization, and widening. The existing instruction handlers are reused.

Arithmetic covers addition, subtraction, multiplication, division, and remainder.
Singleton results wrap exactly like Java int arithmetic. For nonsingleton ranges
that may overflow, the initial implementation conservatively returns top.
Division truncates toward zero using integer calculations, not floating point.
Zero divisors produce an error; nonzero divisor ranges produce normal successors.
Remainder bounds respect the dividend's sign and the divisor's magnitude.

## Combining signs and intervals

`SignInterval` describes one integer through the intersection of both components.
For example, joining -5 and 5 gives:

```text
interval = [-5, 5]
signs    = {negative, positive}
```

Zero is excluded even though it lies between the interval bounds. For `10 / x`,
interval-only analysis allows division by zero. Combined analysis splits the
input into `[-5, -1]` and `[1, 5]` before calculating results and excludes that error.

Construction reduces the components by removing impossible signs and trimming
bounds. Inconsistent pairs normalize to bottom. Joins and meets combine components
and normalize again. Arithmetic evaluates pairs of sign-restricted ranges and
intersects their interval/sign result descriptions. Comparisons evaluate those
same restricted ranges, so they also use both components.

This is a genuine combined domain, not an alias for either component. It remains
non-relational: it does not remember equations between different variables or
that two operands came from the same variable.

## Loop convergence

Loops can produce growing ranges such as `[0, 1]`, `[0, 2]`, `[0, 3]`, ... .
After three growing updates to a saved instruction state, later updates use
widening. A decreasing lower bound jumps to Java's minimum integer, and an
increasing upper bound jumps to its maximum. SignInterval also unions the sign
component and reduces the result. Signs use their ordinary join; boolean,
reference, and string values retain their joined values.

For simplicity, this applies at any repeatedly changing instruction position,
not only identified loop headers. It can sacrifice precision at frequently
visited merge points. The original 300-step analysis budget still applies.
Widening helps the analyzer converge; it does NOT establish Java-program termination.

## Code map

- `abstractions.py`: IntegerAbstraction, SignSet, Interval, SignInterval, StringSet,
  and the independent BooleanSet. Also contains domain-law test helpers.
- `configuration.py`: selection, metadata, scalar construction, and integer-domain
  availability checks. It consumes our options and leaves JPAMB's positional
  arguments (`info`, method, input, step limit) intact.
- `static.py`: state initialization, bytecode handlers, joins, delayed widening,
  worklist execution, and the original analysis/interpreter reporting workflows.
- `string_methods.py`: references, heap-content lookup, reference identity, and
  the model of `String.equals(Object)` including null behavior.

StringSet retains at most eight exact contents, then becomes top. Java null is
tracked on references, not as unknown string contents. Unknown string parameters
may be null; supplied string inputs are exact non-null contents. For example,
unknown `sayHello` input allows normal completion, assertion failure, and a
null-pointer error even though the benchmark only lists non-null examples.

String equality results use the selected integer domain (0/1 intervals, signs,
or combined values), or BooleanSet in string-only mode. Reference identity is
kept separate from string-content equality. State updates copy the heap so one
successor cannot modify another successor's contents.

## Scope and limitations

No branch refinement is added: a condition such as `x > 0` does not narrow the
stored interval on its successful path. There are no relational constraints or
narrowing pass after widening. These can be separate precision improvements.

String method support remains limited to `String.equals(Object)` for supported
string/null operands. Length, concatenation, substring, constructors, arrays,
general calls, and exception handlers are not added by the interval work.
The existing assertion-allocation shortcut and nontermination `unknown` prediction
remain. Unsupported operations or exhausted budgets preserve incomplete/unknown
reporting rather than silently declaring unseen outcomes impossible.

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
