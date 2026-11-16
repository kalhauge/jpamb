# Branch refinement

Implemented on `branch-refinement`, based on merged array-support commit
`19f0e76af98a7c0f5a80d7955e2683c26973c680`. Results recorded on 16 November 2026.

## What changes

Both successors of JVM `If` and `Ifz` are filtered using the condition or its
negation. Impossible successors are omitted. Comparisons support equality,
inequality, and all four ordering operators for numeric/boolean values.

- **Signs:** discard sign alternatives inconsistent with the branch, including
  zero on the successful `n != 0` path.
- **Intervals:** intersect equal operands and tighten both operands' bounds for
  ordering comparisons. Inequality can remove a singleton at an endpoint, but
  cannot represent an interior hole.
- **Sign + interval:** filter sign-separated interval pieces, then reduce the
  resulting product. This retains a hole at zero alongside numeric bounds.
- **Strings:** remember the operands of `String.equals`. A successful equality
  branch intersects possible contents and excludes null operands. A false
  branch excludes a known singleton content when representable, while retaining
  the case of a null argument. Unknown string complements remain unknown.
- **Booleans:** filter the possible true/false values in string-only execution.
- **References:** null tests refine reference nullability, including array
  references. Summary allocation identifiers are not treated as concrete object
  identities. Two loads of the same unchanged local can be compared reflexively.

`State` tracks the local source of each stack value and string-equality predicates
stored in boolean locals. Loads, stores, and `dup` preserve applicable provenance.
An assignment invalidates facts depending on the overwritten local. Joins keep
only matching provenance; widening retains the joined provenance. Computed
arithmetic values lose their source, so the interpreter never assumes that a
computed result is identical to one of its operands. Provenance participates in
state equality but is omitted from the existing `state` trace representation.

All seven domain configurations use the same branch implementation. The
300-step analysis budget, widening policy, unsupported-operation behavior, and
nontermination reporting are unchanged.

## Scores

Paired full-suite analysis runs used **47 methods and three iterations** per
configuration, against the same benchmark and environment. The baseline was
loaded from Git into an isolated source directory, without changing branches.

| Configuration | Before | After | Change |
| --- | ---: | ---: | ---: |
| sign | 146.20 | 154.41 | +8.21 |
| interval | 156.15 | 157.93 | +1.78 |
| string | 72.90 | 72.90 | 0.00 |
| sign,interval | 156.15 | 165.46 | +9.31 |
| sign,string | 148.74 | 156.89 | +8.16 |
| interval,string | 158.62 | 160.38 | +1.76 |
| sign,interval,string | 158.62 | 167.81 | +9.19 |

Signs and the combined domain now exclude unnecessary division-by-zero warnings
in `Dependent.safeDivByN`, `Simple.checkBeforeAssert`,
`Simple.checkBeforeDivideByN`, and `Simple.checkBeforeDivideByN2`. The last method
also loses an unnecessary assertion warning. Interval-only numeric configurations
remove the assertion warning, but cannot express the nonzero hole needed for the
other improvements. This makes the combined domain measurably better than
intervals alone on the existing benchmark.

String-only predictions are unchanged. The existing suite has one String method,
which does not expose the benefit of using a prior equality test to constrain a
later test. Dedicated synthetic interpreter tests cover that behavior in all
four string-enabled configurations, both directly and through a stored boolean.

All analysis reports validated, all iterations agreed on predictions, and no
`no` prediction excluded a benchmark-declared outcome. These checks are not a
formal soundness proof. Aggregate scores use JPAMB's category calibration and
should be interpreted alongside per-method predictions.

## Interpreter validation

Full-suite abstract-interpreter runs used a 300-step trace budget. Each of the
117 per-case statuses matched its baseline, including the existing unsupported
cases. Full-suite commands therefore still exit nonzero; these are not claims
that every Java instruction is supported.

| Configuration | Before | After |
| --- | ---: | ---: |
| sign / interval / sign,interval | 90/117 | 90/117 |
| string | 19/117 | 19/117 |
| sign,string / interval,string / all three | 93/117 | 93/117 |

Static and dynamic automated suites: **239 passed**. New tests cover concrete
containment for every numeric comparison and both branch directions, integer
boundaries, boolean filters, guarded division, nullness, string contents,
stored predicates, reassignment, joins, duplicate operands, and trace schema.

## Reproduce

From the repository root in WSL:

```bash
source .venv/bin/activate
python solutions/static/scripts/compare_branch_refinement.py
```

The script records baseline and refined reports/logs plus `comparison.json` under
`reports/branch-refinement`. Use `--output reports/my-comparison` to retain a
separate run. `--baseline COMMIT` selects a different committed baseline.
The recorded verification run is in `reports/branch-refinement-verified`;
full interpreter logs are in `reports/branch-refinement`.

Run a single configuration:

```bash
jpamb analyse -- static-analysis --abstractions sign,interval,string
jpamb interpret --abstract --max-steps 300 -- static-interpreter --abstractions sign,interval,string
PYTHONPATH=solutions/static/src:solutions/dynamic/src python -m pytest solutions/static/tests solutions/dynamic/tests -q
```

## Remaining precision limits

This is non-relational filtering. It does not preserve general relationships
between different locals, invert arithmetic expressions, propagate array-length
constraints back into heap summaries, or perform a narrowing pass after widening.
Strings do not retain a general disequality relation or a complement of an unknown
set. Heap-content refinement is limited to single-target string parameters and
literals; multi-target references stay conservative. Existing unsupported method
calls and string operations remain unsupported.
