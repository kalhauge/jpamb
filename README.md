# Program analysis with Jev and JPAMB

This is our DTU 02242 project repository, built on
[JPAMB: Java Program Analysis Micro Benchmarks](https://github.com/kalhauge/jpamb).
We are investigating whether Jev-guided selection of static abstractions and
dynamic fuzzers can reduce computation time while preserving behavioural
prediction accuracy. The commands below expose the available analyses; their
existence does not establish that Jev improves results.

JPAMB provides Java methods and expected behaviours for evaluation. An analyzer
receives a method identifier, without its test inputs or annotations, and reports
information about six outcomes: `ok`, `divide by zero`, `assertion error`,
`out of bounds`, `null pointer`, and `*` (nontermination). A bounded execution
timeout is uncertainty about termination, not proof that a method runs forever.

## Start here

Use WSL/Bash from the repository root. For a fresh machine, follow
[setup](docs/setup.md) to prepare the Java benchmark and dependencies first.

### Run a dynamic fuzzer

```bash
uv sync --project solutions/dynamic --group dev
source solutions/dynamic/.venv/bin/activate

jpamb analyse dynamic-analysis --random
jpamb analyse dynamic-analysis --small
jpamb analyse dynamic-analysis --mutation
jpamb analyse dynamic-analysis --random --small --mutation
```

No fuzzer flag defaults to random. Flags can be combined. The selected fuzzers
run sequentially and share a set of observed outcomes; findings are not voted
on or averaged. Mutation uses that shared set as feedback.

**Random runs currently use a fixed seed of 0.** Repeating a command repeats
its generated inputs. There is no `--seed` option yet. Each selected fuzzer
adds its own budget, so combined runs are not equal-budget comparisons.

The [dynamic analyzer guide](solutions/dynamic/README.md) explains supported
inputs, execution limits, testing, and how to construct commands from a selection.

### Run static analysis

Use the static environment when running the static analyzer:

```bash
uv sync --project solutions/static --group dev
source solutions/static/.venv/bin/activate

jpamb analyse static-analysis --abstractions sign
jpamb analyse static-analysis --abstractions interval
jpamb analyse static-analysis --abstractions string
jpamb analyse static-analysis --abstractions sign,interval,string
```

Sign is the default. Sign, interval, and string domains can be selected in any
combination. Integer modes also support one-dimensional int/char arrays using
conservative summaries. See the [static analyzer guide](solutions/static/README.md)
for branch refinement, domain combinations, tests, and limitations.

### Place options correctly

JPAMB options go **before** the analyzer name. Analyzer options go **after** it:

```bash
jpamb analyse --iterations 1 --filter Simple dynamic-analysis --small
jpamb analyse --report dynamic-report.sexp dynamic-analysis --random
```

The explicit separator form, such as `jpamb analyse -- dynamic-analysis --small`,
also works. Reports use S-expressions; `analyse --format=json` is not supported.
Full report validation expects the default three iterations.

## Understand the score before comparing configurations

JPAMB's score is not a count of discovered behaviours. It derives rewards and
penalties from the prediction categories across the evaluated methods. Running
more fuzzers may reveal a behaviour missing from the benchmark's answer key.

One verified omission is `normalizedDistance(0, -2147483648)`: actual Java
execution divides by zero because negating the minimum int overflows back to
itself. The current expected outcomes list only `ok` for this method.

For an explicitly labelled, experimental score with that omission corrected:

```bash
jpamb analyse --true dynamic-analysis --random --small --mutation
```

`--true` changes only an in-memory copy of the expected outcomes. It neither
suppresses discoveries nor changes benchmark files. It is available for any
analyzer; use the same scoring mode across comparisons. Without it, the original
benchmark is used. It cannot be combined with `--report`, because normal report
validation would use the original answer key. This correction is not a claim
that the rest of the benchmark is complete.

A local run on 19 November 2026, with 47 methods and three iterations, scored
124.37 with the original answer key and 157.34 with the correction. These are
configuration-specific observations, not general evidence of Jev's effectiveness.

## Project direction

The planned comparison includes individual analyses, supported fixed
combinations, and Jev selecting both static domains and fuzzers. Holding static
analysis fixed while selecting fuzzers is an additional comparison to isolate
the value of static-domain selection. Include selection overhead in runtime,
use independent expected outcomes, and distinguish timing repetitions from
experiments with different random seeds.

## Documentation

- [Project information](information/README.md): implementation and evaluation notes.
- [Branch refinement](information/branch_refinement.md): static-analysis behaviour and recorded results.
- [Benchmark rules](docs/rules.md): analyzer input/output and scoring protocol.
- [Python setup](docs/python.md): environments and entry points.
- [Interpreter evaluation](docs/interpret.md): concrete and abstract traces.
- [Extending JPAMB](docs/extending-jpamb.md): adding benchmark cases.

The dynamic interpreter supports the instructions needed by the supplied
concrete cases, but is not a complete JVM. Unsupported executions are reported
on stderr. Static analysis has its own documented coverage limits. Read those
limits before interpreting a missed behaviour as evidence of impossibility.
