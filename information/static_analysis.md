# How our static analyzer is implemented

This document collects the implementation explanations previously in the static
solution README. For setup and commands, use the [execution guide](../solutions/static/README.md).
For benchmark interpretation and proposed examples, see [Why scores can be similar](score_similarity.md).

## How array support works

Each array has an abstract length and ONE summary of all element values, using
the chosen integer domain. For example, interval mode describes `[2, 5, 8]` as
length `[3, 3]` and elements `[2, 8]`. Reads return this summary, not an individual
position. New arrays contain Java's initial zero values; an empty array has no
element values.

Supported operations are allocation, array length, element reads/writes, array
parameters, reference loads/stores, null references, and one-word `dup` (used by
compiled array initializers). Accesses check null, negative indices, and indices
at or beyond the length. A possibly valid access can continue while also
reporting an error; a definitely invalid access has no normal successor.

Writes join the new value with the previous element summary. This is deliberately
conservative: a store cannot erase other elements' values. It also handles aliases
and repeated allocations at a single bytecode site safely. Unknown parameters
of the same array type share a heap summary because they may alias; separately
supplied concrete array inputs use separate objects. Updates copy the heap and
widen growing numeric heap summaries as well as local/stack values.

Characters are represented as unsigned UTF-16 code units. Unknown `char[]`
elements cover 0 through 65535. Character stores retain provably in-range values;
otherwise their possible 16-bit truncation is covered by the whole char range.
No hidden interval tracking is added to sign-only mode, so sign mode cannot
usually distinguish different positive indices or array lengths.

Current limitations: no per-index tracking, multidimensional or object arrays,
other primitive array types, or negative-size exception model. A possibly
negative allocation size leaves analysis incomplete because JPAMB has no matching
outcome category. Array loops can still produce extra bounds/assertion warnings
because array summaries and non-relational filtering lose information; ordinary
methods and unsupported casts remain outside this implementation.

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
reference, and string values retain their joined values. Numeric array heap
summaries widen too, with nonnegative lengths and unsigned char ranges preserved.

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
- `array_methods.py`: typed array summaries, creation and inputs, bounds/null
  checks, reads, weak writes, char conversion, joins, and heap widening.
- `string_methods.py`: shared references, string heap-content lookup, reference identity, and
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

Branches now narrow loaded locals, nullness, and supported string predicates; see
[branch refinement](branch_refinement.md). General relational constraints, inverse
arithmetic transfer, and a narrowing pass after widening remain unsupported.

String method support remains limited to `String.equals(Object)` for supported
string/null operands. String length, concatenation, substring, constructors,
general calls, and exception handlers remain unsupported. Array length is
supported independently of string length.
The existing assertion-allocation shortcut and nontermination `unknown` prediction
remain. Unsupported operations or exhausted budgets preserve incomplete/unknown
reporting rather than silently declaring unseen outcomes impossible.
