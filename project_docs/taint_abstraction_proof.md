# Correctness of the Taint Abstraction

## Scope

This document proves that the proposed label-set abstraction is a sound over-approximation of explicit taint dependencies in the modeled JVM semantics. The result is intentionally narrower than a proof of the complete security tool: it shows that the `labels` component of `TaintValue` and its transfer functions do not discard a concrete dependency represented by the model. Abstract reference targets are retained separately to locate heap cells; proving the precision of points-to information is outside the scope of this label-set proof. Call-graph construction, library summaries, sink specifications, and dynamic exploit confirmation are separate concerns and appear as assumptions at the end.

## Concrete and abstract domains

Let `L = {p0, ..., pn}` be the finite set of source labels assigned to the parameters of the JPAMB entry method. Let `V` be the set of concrete JVM values.

A concrete tagged value is a pair `(v, D)`, where `v` is a value in `V` and `D` is a subset of `L` containing the sources on which `v` depends. The collecting concrete domain is

`C = P(V x P(L))`,

ordered by set inclusion.

The abstract domain retains only possible source dependencies:

`A = P(L)`.

For `T1, T2` in `A`, define

```text
T1 <= T2       iff T1 is a subset of T2
T1 join T2     = T1 union T2
T1 meet T2     = T1 intersection T2
bottom         = empty set
top            = L
```

An abstract element `T` means that the represented value may depend on any subset of the labels in `T`. The empty set means that a reachable value has no known source dependency. An unreachable program state is represented separately by the absence of a state at that program point; it must not be confused with an untainted value.

## Lemma 1: the abstract domain is a lattice

Set inclusion is reflexive, antisymmetric, and transitive, so `(P(L), subset)` is a partially ordered set. For every pair `T1` and `T2`, their union is the least set containing both and is therefore their least upper bound. Their intersection is the greatest set contained in both and is therefore their greatest lower bound. The empty set is contained in every element and is bottom, while every element is contained in `L`, which is top. Therefore

`(P(L), subset, union, intersection, empty set, L)`

is a lattice. It is finite because `L` is finite.

## Abstraction and concretization

Define the abstraction function `alpha : C -> A` by

`alpha(X) = union of D for every (v, D) in X`.

It forgets concrete values and correlations between individual values and dependency sets, retaining every source dependency that occurs in `X`.

Define the concretization function `gamma : A -> C` by

`gamma(T) = {(v, D) | v in V and D is a subset of T}`.

Thus, `gamma(T)` contains every concrete tagged value whose exact dependencies are allowed by `T`.

## Theorem 1: Galois connection

For every `X` in `C` and `T` in `A`,

`alpha(X) is a subset of T` if and only if `X is a subset of gamma(T)`.

### Proof

Assume first that `alpha(X)` is a subset of `T`. Take any `(v, D)` in `X`. By the definition of `alpha`, `D` is a subset of `alpha(X)`. Hence `D` is a subset of `T`, and by the definition of `gamma`, `(v, D)` belongs to `gamma(T)`. Since this holds for every element of `X`, `X` is a subset of `gamma(T)`.

Conversely, assume that `X` is a subset of `gamma(T)`. For every `(v, D)` in `X`, membership in `gamma(T)` implies that `D` is a subset of `T`. The union of sets that are all subsets of `T` is itself a subset of `T`. By the definition of `alpha`, this union is `alpha(X)`. Therefore `alpha(X)` is a subset of `T`.

This proves the equivalence and establishes a Galois connection between `C` and `A`.

## Corollary 1: abstraction does not discard represented dependencies

Taking `T = alpha(X)` in Theorem 1 gives

`X is a subset of gamma(alpha(X))`.

The abstraction may lose concrete values and correlations, so equality is not required. Concretizing an abstraction may introduce additional possibilities, but it still contains every original concrete tagged value.

## Abstract transfer functions

The analysis uses the following transfer rules for explicit data dependencies.

### Constants

A constant has no dependency on an entry parameter:

`const#(v) = empty set`.

This exactly abstracts its concrete dependency set.

### Copying operations

Operations such as loads, stores, and casts preserve the dependency set:

`copy#(T) = T`.

They therefore preserve the abstraction relation.

### Data-combining operations

For an operation whose result may depend on each of its operands, including arithmetic and string concatenation, define

`op#(T1, ..., Tk) = T1 union ... union Tk`.

In the tagged concrete semantics, applying the corresponding operation to `(v1, D1), ..., (vk, Dk)` produces a result tagged with `D1 union ... union Dk`. Consequently, for collecting operand sets `X1, ..., Xk`,

`alpha(op(X1, ..., Xk))` is a subset of `op#(alpha(X1), ..., alpha(Xk))`.

Therefore the abstract operation cannot omit a dependency produced by its concrete counterpart.

### Control-flow merges

If two control-flow paths produce abstract values `T1` and `T2`, the merged value is

`T1 join T2 = T1 union T2`.

Every concrete value arriving from either path is represented by the result. This is the source of intentional path insensitivity and may introduce dependencies that cannot occur together, but it does not remove dependencies.

### Calls and returns

At a call, each argument label set is copied to the corresponding callee parameter. On return, the return-value label set is copied to every represented return site. Because copying preserves labels and states from different callers are combined by join, this context-insensitive treatment may lose precision but retains all represented explicit dependencies.

### Heap fields and arrays

A reference-valued `TaintValue` contains both a label set and a finite set of abstract allocation sites. The allocation sites determine which heap cells may be accessed; they are not themselves source labels.

For a field read, the analysis joins the field values stored at every possible target and conservatively combines their labels with the labels of the receiver reference:

`getfield#(reference, field) = labels(reference) union joined labels of target.field`.

For a field write, every possible target is weakly updated. The stored labels include both the written value labels and the receiver labels, preserving a possible dependency on which object is selected:

`heap'(target.field) = heap(target.field) union labels(reference) union labels(value)`.

Arrays initially use one abstract contents cell per allocation site. Array reads and writes follow the same rules, additionally joining index labels when the selected element may depend on a tainted index. These rules may introduce additional dependencies, but they do not remove a dependency represented by the concrete access.

### Security sinks and findings

When an invocation matches a configured security sink, its argument values are removed from the operand stack according to the normal JVM calling convention. Before they are removed, the analysis records a `TaintFinding` containing the sink location and the argument labels. Removing the stack value therefore does not discard the result of the analysis: the dependency is preserved in the finding and, when specified by the method summary, in the invocation's abstract return value.

### Trusted summaries and sanitizers

A library summary must provide a transfer function satisfying the same over-approximation condition. A sanitizer may return the empty set only under the explicit assumption that its specification guarantees that the returned value is safe according to the chosen security policy. Incorrect summaries or sanitizer specifications are outside the guarantee of this proof.

## Lifting the abstraction to JVM states

The value abstraction is lifted component-wise to abstract locals, operand stacks, and heaps. Locals and stack positions contain `TaintValue` instances, each consisting of a label set and, for references, possible allocation sites. Heap cells are addressed by an allocation site together with a field or abstract array-content identifier. An abstract state is

`State# = Locals# x Stack# x Heap#`,

and the global analysis state maps each program counter to an abstract state. Ordering and join are defined point-wise. Reference targets are joined by set union, while the label component uses the taint lattice defined above. Therefore, if every concrete component is represented by its corresponding abstract component before a step, and the instruction transfer function satisfies the local over-approximation property, every concrete successor is represented by an abstract successor.

## Theorem 2: preservation over execution steps

Assume that the initial abstract state represents every modeled concrete initial state and that every supported instruction and method summary satisfies

`alpha(step(S)) <= step#(alpha(S))`.

Then, after any finite number of execution steps, every reachable concrete tagged state is represented by the corresponding abstract state.

### Proof sketch

The proof is by induction on the number of concrete steps. The base case follows from the construction of the initial state: parameter `i` receives `{pi}`, constants have no source labels, and unreadable or unreachable locations are represented separately rather than as ordinary untainted values. For the induction step, assume that the abstract state represents the concrete state before an instruction. By the local correctness of the instruction transfer function, every concrete successor is represented by an abstract successor. Joining that successor into the stored state can only add information, so the representation remains valid. The property therefore holds for every finite execution prefix.

## Fixpoint and termination

The worklist algorithm repeatedly joins incoming states at program points and reprocesses a point only when its stored state grows. All transfer functions are monotone: adding possible dependencies to an input cannot remove dependencies from the output.

The label lattice is finite, as are the program points, local-variable positions, valid operand-stack positions, allocation sites, and context-insensitive return locations in the analyzed program. Hence the global abstract state has finite height. It can grow only finitely many times, so the worklist eventually becomes empty and the analysis reaches a fixpoint without widening.

At that fixpoint, Theorem 2 implies that every modeled reachable concrete state is represented. In particular, if a concrete value reaching a configured security sink depends on source `pi`, the corresponding abstract sink value contains `pi`.

## Assumptions and limitations

The guarantee is relative to the modeled semantics. It assumes correct handling of supported JVM instructions, a sufficiently complete call graph, correct reflection and deserialization summaries, correct sink specifications, and trustworthy sanitizer specifications. The initial analysis tracks explicit data flows but not implicit control dependencies. Unsupported library behavior and missing call-graph edges may invalidate whole-tool soundness even though the label-set abstraction itself satisfies the properties proved above.
