"""Sound, non-relational branch filters and transient operand provenance."""

from dataclasses import dataclass, replace

from abstractions import (
    SIGN_RANGES,
    BooleanSet,
    Interval,
    SignInterval,
    SignSet,
    StringSet,
)
from string_methods import AbstractReference, contents

import jvm


@dataclass(frozen=True)
class Local:
    index: int


@dataclass(frozen=True)
class StringEquals:
    left: AbstractReference
    right: AbstractReference
    left_origin: object
    right_origin: object


def depends_on(origin, index):
    if isinstance(origin, Local):
        return origin.index == index
    if isinstance(origin, StringEquals):
        return depends_on(origin.left_origin, index) or depends_on(
            origin.right_origin, index
        )
    return False


NEGATE = dict(
    zip(
        [
            jvm.CmpOpr.Eq,
            jvm.CmpOpr.Ne,
            jvm.CmpOpr.Lt,
            jvm.CmpOpr.Le,
            jvm.CmpOpr.Gt,
            jvm.CmpOpr.Ge,
        ],
        [
            jvm.CmpOpr.Ne,
            jvm.CmpOpr.Eq,
            jvm.CmpOpr.Ge,
            jvm.CmpOpr.Gt,
            jvm.CmpOpr.Le,
            jvm.CmpOpr.Lt,
        ],
    )
)


def interval_pair(a, b, op):
    if a.is_bottom() or b.is_bottom():
        return Interval.bot(), Interval.bot()
    if op == jvm.CmpOpr.Eq:
        return a & b, a & b
    if op == jvm.CmpOpr.Ne:

        def exclude(x, y):
            if y.min != y.max:
                return x
            if x.min == y.min:
                return Interval(x.min + 1, x.max)
            if x.max == y.min:
                return Interval(x.min, x.max - 1)
            return x  # An interval cannot represent an interior hole.

        return exclude(a, b), exclude(b, a)
    if op in (jvm.CmpOpr.Gt, jvm.CmpOpr.Ge):
        y, x = interval_pair(
            b, a, jvm.CmpOpr.Lt if op == jvm.CmpOpr.Gt else jvm.CmpOpr.Le
        )
        return x, y
    gap = int(op == jvm.CmpOpr.Lt)
    return Interval(a.min, min(a.max, b.max - gap)), Interval(
        max(b.min, a.min + gap), b.max
    )


def parts(value):
    if isinstance(value, SignInterval):
        return [part for _, part in value.parts()]
    if isinstance(value, SignSet):
        return [SIGN_RANGES[s] for s in value.signs]
    return [value]


def from_parts(original, ranges):
    bounds = Interval.bot()
    signs = set()
    for part in ranges:
        if part.is_bottom():
            continue
        bounds = bounds | part
        signs.update(s for s, r in SIGN_RANGES.items() if not (part & r).is_bottom())
    if isinstance(original, SignInterval):
        return SignInterval(SignSet(frozenset(signs)), bounds)
    if isinstance(original, SignSet):
        return SignSet(frozenset(signs))
    return bounds


def filter_pair(a, b, op, answer):
    """Project satisfying pairs onto each operand, preserving representable holes."""
    if not answer:
        op = NEGATE[op]
    if isinstance(a, BooleanSet):
        pairs = [
            (x, y)
            for x in a.values
            for y in b.values
            if True
            in BooleanSet(frozenset({x})).compare(BooleanSet(frozenset({y})), op)
        ]
        return BooleanSet(frozenset(x for x, _ in pairs)), BooleanSet(
            frozenset(y for _, y in pairs)
        )
    if isinstance(a, AbstractReference):
        # Summary allocation IDs are not concrete identities. Only nullness can
        # safely be propagated without a must-alias relation.
        null = AbstractReference(frozenset(), True)

        def against_null(x):
            return null if op == jvm.CmpOpr.Eq else replace(x, may_be_null=False)

        if b == null:
            return against_null(a), b
        if a == null:
            return a, against_null(b)
        if op == jvm.CmpOpr.Eq:
            return replace(a, may_be_null=a.may_be_null and b.may_be_null), replace(
                b, may_be_null=a.may_be_null and b.may_be_null
            )
        return a, b
    left, right = [], []
    for x in parts(a):
        for y in parts(b):
            x1, y1 = interval_pair(x, y, op)
            if not x1.is_bottom() and not y1.is_bottom():
                left.append(x1)
                right.append(y1)
    return from_parts(a, left), from_parts(b, right)


def empty(value):
    if isinstance(value, AbstractReference):
        return not value.targets and not value.may_be_null
    if isinstance(value, BooleanSet):
        return not value.values
    return value == value.bot()


def apply_value(state, origin, value):
    if empty(value):
        return None
    if isinstance(origin, Local):
        values = list(state.locals)
        values[origin.index] = value
        # Other copies of the same local on the operand stack remain correlated.
        stack = tuple(
            value if o == origin else v for v, o in zip(state.stack, state.origins)
        )
        state = replace(state, locals=tuple(values), stack=stack)
        return apply_value(state, state.predicates[origin.index], value)
    if isinstance(origin, StringEquals):
        # equals returns exactly 0 or 1, even when the numeric abstraction is signs.
        from jvm.state import StackInt

        answers = (
            {bool(x) for x in (0, 1) if StackInt(x) in value}
            if not isinstance(value, BooleanSet)
            else set(value.values)
        )
        if len(answers) == 1:
            return refine_strings(state, origin, answers.pop())
    return state


def refine_strings(state, predicate, answer):
    left, right = predicate.left, predicate.right
    # Reaching a boolean result already implies a non-null receiver.
    state = apply_value(state, predicate.left_origin, replace(left, may_be_null=False))
    if state is None:
        return None
    if answer:
        state = apply_value(
            state, predicate.right_origin, replace(right, may_be_null=False)
        )
        if state is None:
            return None
    a, b = contents(left, state.heap), contents(right, state.heap)
    if answer:
        narrowed_a = narrowed_b = a & b
    else:

        def excluding(x, y):
            if x.values is not None and y.values is not None and len(y.values) == 1:
                return StringSet(x.values - y.values)
            return x

        # A null argument makes equals false independently of its contents.
        narrowed_a = a if right.may_be_null else excluding(a, b)
        narrowed_b = excluding(b, a)
    heap = dict(state.heap)
    for reference, value in ((left, narrowed_a), (right, narrowed_b)):
        # Do not strongly refine a summary shared by multiple possible objects.
        if len(reference.targets) == 1:
            target = next(iter(reference.targets))
            if target.startswith(("parameter:", "literal:")):
                heap[target] = heap[target] & value
    if answer and (narrowed_a == StringSet.bot() or narrowed_b == StringSet.bot()):
        return None
    return replace(state, heap=heap)


def branch(state, left, right, left_origin, right_origin, op, answer):
    if (
        left_origin is not None
        and left_origin == right_origin
        and isinstance(left_origin, Local)
    ):
        # Comparing two loads of the same unchanged local is reflexive.
        truth = op in (jvm.CmpOpr.Eq, jvm.CmpOpr.Le, jvm.CmpOpr.Ge)
        if answer != truth:
            return None
    a, b = filter_pair(left, right, op, answer)
    state = apply_value(state, left_origin, a)
    return None if state is None else apply_value(state, right_origin, b)
