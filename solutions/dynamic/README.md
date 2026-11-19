# Dynamic analyzer

From the repository root, set up an environment containing this checkout:

```bash
uv sync --project solutions/dynamic --group dev
source solutions/dynamic/.venv/bin/activate
jpamb analyse dynamic-analysis --random
jpamb analyse dynamic-analysis --small
jpamb analyse dynamic-analysis --mutation
```

Omitting the fuzzer flags defaults to random. Flags combine, for example:

```bash
jpamb analyse dynamic-analysis --small --mutation
jpamb analyse --iterations 1 --filter Simple dynamic-analysis --random --small --mutation
```

Put JPAMB options BEFORE `dynamic-analysis`; everything after the executable
is forwarded to it. The explicit `jpamb analyse -- dynamic-analysis --small`
form also works. `dynamic-analysis --help` describes the available flags.

Jev can produce an argument list such as
`["jpamb", "analyse", "dynamic-analysis", "--small", "--mutation"]`.
For a single method, invoke
`dynamic-analysis --small 'package.Class.method:(I)V'` with the actual identifier.

Selected fuzzers run in fixed order: random, small, mutation. Outcomes are
combined and emitted once through the existing JPAMB protocol. Metadata tags
reflect the selected strategies. Each strategy starts with seed 0, so repeated commands generate the same inputs.
There is currently no `--seed` flag. Mutation corpus growth depends on behaviours
found by earlier fuzzers, so its inputs can differ between standalone and combined
runs even with the same seed. Existing
budgets are unchanged: 10 random trials, small depth 3, 30 mutation attempts
(after seed inputs), and 200 interpreter steps per input. Combined strategies
have cumulative budgets; account for that in comparisons.

Small and mutation currently support only int/boolean parameters. Random also
supports the existing string/array input types. Selecting a strategy does not
extend the interpreter's opcode support. A step limit produces `*;timeout`,
not proof of nontermination.

## Execution support and testing

The dynamic interpreter now supports integer loads/stores, signed 32-bit
arithmetic (including Java division/remainder), comparisons, branches,
increments, narrowing casts, void/value returns, static calls, assertions,
int/char arrays and null/bounds checks, and String.equals. It remains a subset
of the JVM, not a general Java runtime. Unsupported executions are diagnosed
on stderr and skipped without discarding earlier observations. Large or negative
array allocations are unsupported; unsupported execution is never labelled ok.
Per-instruction debug printing was removed from normal fuzzing execution.

Run regressions, including all supplied concrete cases from a built checkout:

```bash
JPAMB_TEST_WORKDIR="$PWD" \
  solutions/dynamic/.venv/bin/python -m pytest solutions/dynamic/tests -q
```

The concrete-case test uses a larger step allowance to validate semantics.
Production fuzzing still allows 200 steps per input, so some terminating
methods will produce timeout observations. Random fuzzing need not discover
rare strings or numeric values even when their execution is supported.

Benchmark note: normalizedDistance(0, -2147483648) can divide by zero because
negating Java's minimum int overflows back to itself. The current benchmark's
method-level expected outcomes list only ok. This can penalize a valid witness;
no benchmark annotations were changed by this interpreter fix.

## Experimental corrected score: --true

```bash
jpamb analyse --true dynamic-analysis --random --small --mutation
```

`--true` is a JPAMB option, so it goes BEFORE `dynamic-analysis`. It adds
`divide by zero` to normalizedDistance's method-level expected outcomes in an
in-memory copy of the benchmark. It does not suppress findings, skip the method,
change analyzer behaviour, or edit benchmark files. The output explicitly marks
this as experimental corrected scoring. Without the flag, scoring is unchanged.
The correction also applies to other analyzers for a consistent comparison.

The verified witness is normalizedDistance(0, -2147483648): negating the minimum
Java int leaves it negative due to overflow, so the x >= y branch divides by
x = 0. The existing benchmark's answer key omits that outcome.

`--true` cannot be combined with `--report`: report validation uses the original
benchmark, so such an export would not reproduce the corrected score. Step-wise
runs use a separate cache for corrected scoring.
