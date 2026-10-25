# Taint Analysis Architecture - Initial Decisions

## Purpose

The static taint analysis identifies which parameters of a JPAMB entry method may influence values passed to security-sensitive operations. Its findings guide the fuzzer toward relevant methods, parameters, and sinks. Dynamic execution remains responsible for confirming that a reported flow is exploitable.

The analysis is a **may-analysis**: it over-approximates possible flows. Within the supported model, a concrete taint flow must also appear in the abstract result. The analysis may therefore report infeasible flows, which the fuzzer can later reject or leave unverified.

## Scope and precision

The initial analysis has the following properties:

- One JPAMB entry method is analyzed at a time.
- Every entry-method parameter receives a distinct source label, such as `p0` or `p1`.
- The analysis is flow-sensitive: it maintains an abstract state at each program counter.
- It is initially path-insensitive: states from different branches are joined.
- It tracks explicit data flows only.
- It is interprocedural but initially context-insensitive: calls to the same method may be joined.

Not tracking implicit flows is a deliberate limitation. For example, a parameter that only controls whether a sink is reached may not appear among the labels passed to that sink. The fuzzer should therefore continue mutating every input parameter, while prioritizing parameters identified by explicit taint flows. Full control-dependence tracking may be added later if needed.

## Taint domain

Let `L = {p0, ..., pn}` be the finite set of labels assigned to the parameters of the entry method. The abstract taint domain is the powerset of `L`:

`T = P(L)`

An element records all sources on which a value may depend. The lattice is:

- order: `T1 <= T2` iff `T1` is a subset of `T2`;
- join: `T1 join T2 = T1 union T2`;
- meet: `T1 meet T2 = T1 intersection T2`;
- bottom: the empty set, meaning no known tainted dependency;
- top: `L`, meaning possible dependency on every source.

Join is used when control-flow paths merge. Meet is part of the lattice definition but is not normally used to merge states in this may-analysis.

## Abstract values and states

The implementation will introduce a `TaintValue`, separate from the existing sign-analysis `StackValue`. Conceptually it contains:

```text
TaintValue
  labels: TaintSet
  references: optional finite set of allocation sites
```

This separation is necessary because a JVM reference can simultaneously point to abstract heap locations and carry taint labels. The exact treatment of null and unknown references will be finalized before implementation.

An abstract JVM state contains abstract locals, an abstract operand stack, and an abstract heap. The whole analysis maps each program counter to one such state:

```text
PC -> (locals, operand stack, heap)
```

Heap objects are represented by allocation sites, identified by the program counter of the allocating instruction. This keeps the abstract heap finite, at the cost of merging objects created at the same site.

## Propagation rules

Constants start with no labels, while entry-method parameter `i` starts with `{pi}`. Loads, stores, casts, and returns preserve labels. Operations such as string concatenation combine operand labels using union. Calls propagate argument labels to callee parameters and return labels back to callers. At control-flow merges, states are joined component-wise.

Security sinks are defined explicitly together with their sensitive argument positions. Initial examples include reflection and the project's simulated deserialization operations. `Vulnerable.canary()` is treated separately as the dynamic exploit oracle: a security sink indicates a potentially dangerous flow, while the canary confirms that the simulated exploit succeeded.

Unsupported library behavior, reflection, and simulated deserialization are handled through trusted method summaries. Only methods explicitly configured as trusted sanitizers may remove taint. Ordinary comparisons, allowlists, or regular-expression checks are not automatically assumed to sanitize a value. The analysis guarantee is therefore conditional on the correctness of sink, sanitizer, and library summaries.

## Fixpoint computation

The analysis uses the existing worklist architecture. A successor program point is processed again only when joining an incoming state makes its stored state larger. The analysis terminates when the worklist is empty, rather than after an arbitrary number of steps.

No widening is required for the taint domain. The label set, program points, allocation sites, and context-insensitive return locations are finite, so abstract states can grow only a finite number of times before reaching a fixpoint.

## Output for the fuzzer

The internal result is a structured set of analysis hints. Each finding should contain at least:

```text
TaintFinding
  sink method and program counter
  labels reaching the sink
  relevant entry parameters
  call-graph distance to the sink
```

The call-graph distance is the minimum number of call edges from a method to the sink. It is computed from the call graph, not from the taint lattice, and can be used as part of the fuzzer's fitness function. A single call path is not required because a path-insensitive may-analysis may represent several paths simultaneously.

Python dataclasses will be used internally. S-expressions may be used for persistence and debugging to remain consistent with the existing framework. The combined analyzer will eventually translate its result into the standard JPAMB prediction format.

## Decisions deferred beyond the initial implementation

The following extensions are intentionally deferred: implicit-flow tracking, path sensitivity, 1-CFA or deeper context sensitivity, precise string-content abstraction, intra-procedural distance metrics, worklist ordering optimizations, and complete modeling of Java libraries. They should be reconsidered only if evaluation shows that the initial analysis is too imprecise or inefficient.
