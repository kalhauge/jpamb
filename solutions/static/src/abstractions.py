from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, Self

import jvm
import jvm.state as jvms


class Poset(ABC):
    @abstractmethod
    def __eq__(self, other: Self) -> bool: ...

    @abstractmethod
    def __lt__(self, other: Self) -> bool: ...

    def __le__(self, other: Self) -> bool:
        return self == other or self < other

    @abstractmethod
    def __gt__(self, other: Self) -> bool: ...

    def __ge__(self, other: Self) -> bool:
        return self == other or self > other


def is_reflexive(a: Poset):
    # Checking if the relation is reflexive (a == a)
    assert a == a, f"Reflexivity check failed: Element {a} is not related to itself."  # noqa: PLR0124


def is_antisymmetric(a: Poset, b: Poset):
    if a != b:
        # Checking that if a <= b and b <= a, then a must equal b
        assert not (a <= b <= a), (
            f"Antisymmetry violation: Found elements where {a} <= {b} and {b} <= {a}, "
            f"but {a} != {b}."
        )


def is_transitive(a: Poset, b: Poset, c: Poset):
    if a <= b <= c:
        # Checking that if a <= b and b <= c, then a <= c
        assert a <= c, (
            f"Transitivity violation: Found path {a} <= {b} and {b} <= {c}, "
            f"but {a} is not related to {c}."
        )


def is_poset(a: Poset, b: Poset, c: Poset):
    for x in [a, b, c]:
        is_reflexive(x)

    for x in [b, c]:
        is_antisymmetric(a, x)

    is_transitive(a, b, c)


class Lattice(Poset):
    @classmethod
    @abstractmethod
    def top(cls) -> Self:
        raise NotImplementedError(f"top: {cls}")

    @classmethod
    def bot(cls) -> Self:
        return cls.abstract([])

    @abstractmethod
    def __or__(self, other: Self) -> Self: ...

    @abstractmethod
    def __and__(self, other: Self) -> Self: ...


def is_lattice_identities(a: Lattice):
    # Top element identity checks
    assert (a | a.top()) == a.top(), (
        f"Top identity fail: ({a} | {a.top()}) -> {a | a.top()} != {a.top()}"
    )
    assert (a.top() | a) == a.top(), (
        f"Top identity fail (commute): ({a.top()} | {a}) != {a.top()}"
    )
    assert (a & a.top()) == a, f"Top identity fail (meet): ({a} & {a.top()}) != {a}"
    assert (a.top() & a) == a, (
        f"Top identity fail (meet commute): ({a.top()} & {a}) != {a}"
    )

    # Bottom element identity checks
    assert (a & a.bot()) == a.bot(), (
        f"Bottom identity fail: ({a} & {a.bot()}) != {a.bot()}"
    )
    assert (a.bot() & a) == a.bot(), (
        f"Bottom identity fail (commute): ({a.bot()} & {a}) != {a.bot()}"
    )
    assert (a.bot() | a) == a, f"Bottom identity fail (join): ({a.bot()} | {a}) != {a}"
    assert (a | a.bot()) == a, (
        f"Bottom identity fail (join commute): ({a} | {a.bot()}) != {a}"
    )


def is_lattice(a: Lattice, b: Lattice, c: Lattice):
    for x in [a, b, c]:
        is_lattice_identities(x)

    if not (a | b <= c):
        # Calculate values for the error message
        assert not (a <= c and b <= c), (
            f"Upper bound check failed: ({a} | {b}) -> {a | b} is not <= {c}. "
            f"Check individual bounds: {a <= c=}, {b <= c=}."
        )

    if not (c <= a & b):
        # Calculate values for the error message
        assert not (c <= a and c <= b), (
            f"Lower bound check failed: {c} is not <= ({a} & {b}) -> {a & b}. "
            f"Check individual bounds: {c <= a=}, {c <= b=}."
        )


class Abstraction(ABC):
    """This is the minimal interface for an abstraction."""

    @classmethod
    @abstractmethod
    def abstract(cls, values: Iterable[jvms.StackValue]) -> Self:
        raise NotImplementedError(f"abstract: {cls}")

    @abstractmethod
    def __contains__(self, value: jvms.StackValue) -> bool: ...


def is_galoi(a: set[jvms.StackValue], b: Abstraction):
    alpha_a = type(b).abstract(a)

    for value in a:
        assert value in alpha_a, f"{value} not in {a}"

    if alpha_a <= b:
        for value in a:
            assert value in b, f"{value} not in {b}"


type Sign = Literal[-1, 0, 1]


def to_sign(value: jvms.StackValue) -> Sign:
    match value:
        case int(v):
            return (v > 0) - (v < 0)
        case jvms.StackInt(v):
            return (v > 0) - (v < 0)
        case a:
            raise NotImplementedError(f"Unsupported value {value!r}")


@dataclass(frozen=True, order=True)
class SignSet(Abstraction, Lattice):
    signs: frozenset[Sign]

    def __str__(self):
        return f"{{{''.join(z for z, b in zip('-0+', [-1, 0, 1]) if b in self.signs)}}}"

    def __sexpr__(self):
        return str(self)

    @classmethod
    def from_sign(cls, code):
        return cls(frozenset(b for z, b in zip("-0+", [-1, 0, 1]) if z in code))

    @classmethod
    def abstract(cls, values: Iterable[jvms.StackValue]) -> Self:
        signs = set()
        for value in values:
            signs.add(to_sign(value))
        return cls(frozenset(signs))

    def __contains__(self, value: jvms.StackValue) -> bool:
        return to_sign(value) in self.signs

    @classmethod
    def top(cls) -> bool:
        return cls(frozenset([-1, 0, 1]))

    def __or__(self, other: "SignSet") -> "SignSet":
        if not isinstance(other, SignSet):
            return NotImplemented

        return SignSet(self.signs | other.signs)

    def __and__(self, other: "SignSet") -> "SignSet":
        if not isinstance(other, SignSet):
            return NotImplemented

        return SignSet(self.signs & other.signs)

    def arithmetic(self, other: "SignSet", opr: jvm.BinaryOpr) -> tuple["SignSet", set[str]]:
        match opr:
            case jvm.BinaryOpr.Add:
                output = set()
                if 1 in self.signs:
                    output.add(1)
                    if -1 in other.signs:
                        output.update([0, -1])

                if -1 in self.signs:
                    output.add(-1)
                    if 1 in other.signs:
                        output.update([0, 1])

                if 0 in self.signs:
                    output.update(other.signs)

                return (SignSet(output), set())

            case jvm.BinaryOpr.Sub:
                output = set()
                if 1 in self.signs:
                    output.add(1)
                    if 1 in other.signs:
                        output.update([0, -1])

                if -1 in self.signs:
                    output.add(-1)
                    if -1 in other.signs:
                        output.update([0, 1])

                if 0 in self.signs:
                    output.update(-s for s in other.signs)
                
                return (SignSet(output), set())

            case jvm.BinaryOpr.Mul:
                output = set()

                if 1 in self.signs:
                    output.update(other.signs)

                if 0 in self.signs:
                    output.add(0)

                if -1 in self.signs:
                    output.update(-s for s in other.signs)

                return (SignSet(output), set())


            case jvm.BinaryOpr.Div:
                output = set()
                errors = set()

                for x in self.signs:
                    for y in other.signs:
                        if y == 0:
                            errors.add("divide by zero")
                            continue

                        if x == 0:
                            output.add(0)
                        elif x == y:
                            # Same sign: integer division may be 0 or positive
                            output.update([0, 1])
                        else:
                            # Different signs: integer division may be 0 or negative
                            output.update([0, -1])

                return (SignSet(frozenset(output)), errors)


            case jvm.BinaryOpr.Rem:
                output = set()
                errors = set()

                for x in self.signs:
                    for y in other.signs:
                        if y == 0:
                            errors.add("divide by zero")
                            continue

                        if x == 0:
                            output.add(0)
                        elif x == 1:
                            output.update([0, 1])
                        elif x == -1:
                            output.update([-1, 0])

                return (SignSet(frozenset(output)), errors)
            case _:
                raise NotImplementedError(f"TODO: {opr}")

    def compare(self, other: "SignSet", opr: jvm.CmpOpr) -> Iterable[bool]:
        match opr:
            case jvm.CmpOpr.Le:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x <= y)
                            continue
                        if x <= y:
                            cases.add(True)
                        if x >= y:
                            cases.add(False)
                return cases
            
            case jvm.CmpOpr.Ne:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x==0 and y==0:
                            cases.add(False)
                            continue
                        if x == y:
                            cases.add(True)
                            cases.add(False)
                            continue
                        if x != y:
                            cases.add(True)
                return cases

            case jvm.CmpOpr.Lt:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x < y)
                            continue
                        if x < y:
                            cases.add(True)
                        if x > y:
                            cases.add(False)
                        if x == y:
                            cases.add(True)
                            cases.add(False)

                return cases
            
            case jvm.CmpOpr.Gt:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x > y)
                            continue
                        if x > y:
                            cases.add(True)
                        if x < y:
                            cases.add(False)
                        if x == y:
                            cases.add(True)
                            cases.add(False)

                return cases

            case jvm.CmpOpr.Ge:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x >= y)
                            continue
                        if x >= y:
                            cases.add(True)
                        if x <= y:
                            cases.add(False)
                return cases

            case jvm.CmpOpr.Eq:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x==0 and y==0:
                            cases.add(True)
                            continue
                        if x == y:
                            cases.add(True)
                            cases.add(False)
                            continue
                        if x != y:
                            cases.add(False)
                return cases

            case jvm.CmpOpr.Lt:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x < y)
                            continue
                        if x < y:
                            cases.add(True)
                        if x > y:
                            cases.add(False)
                        if x == y:
                            cases.add(True)
                            cases.add(False)

                return cases
            
            case jvm.CmpOpr.Gt:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x > y)
                            continue
                        if x > y:
                            cases.add(True)
                        if x < y:
                            cases.add(False)
                        if x == y:
                            cases.add(True)
                            cases.add(False)

                return cases

            case jvm.CmpOpr.Ge:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x == 0 or y == 0:
                            cases.add(x >= y)
                            continue
                        if x >= y:
                            cases.add(True)
                        if x <= y:
                            cases.add(False)
                return cases

            case jvm.CmpOpr.Eq:
                cases = set()
                for x in self.signs:
                    for y in other.signs:
                        if x==0 and y==0:
                            cases.add(True)
                            continue
                        if x == y:
                            cases.add(True)
                            cases.add(False)
                            continue
                        if x != y:
                            cases.add(False)
                return cases

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Interval(Abstraction, Lattice):
    min: int | None
    max: int | None

    def __str__(self):
        return f"{self.min if self.min is not None else '-inf'}:{self.max if self.max is not None else 'inf'}"

    def __sexpr__(self):
        return str(self)

    @classmethod
    def abstract(cls, values: Iterable[jvms.StackValue]) -> Self:
        integers = [value.value for value in values if isinstance(value, jvms.StackInt)]

        if not integers:
            return cls(1, 0)

        return cls(min(integers), max(integers))

    def __contains__(self, value: jvms.StackValue) -> bool:
        if not isinstance(value, jvms.StackInt):
            return False

        if self.min is not None and value.value < self.min:
            return False

        if self.max is not None and value.value > self.max:
            return False

        return True

    @classmethod
    def top(cls) -> Self:
        return cls(None, None)

    def __or__(self, other: "Interval") -> "Interval":
        # bottom | x = x
        if self.min is not None and self.max is not None and self.min > self.max:
            return other

        if other.min is not None and other.max is not None and other.min > other.max:
            return self

        # Lower bound: choose the smallest
        if self.min is None or other.min is None:
            new_min = None
        else:
            new_min = min(self.min, other.min)

        # Upper bound: choose the largest
        if self.max is None or other.max is None:
            new_max = None
        else:
            new_max = max(self.max, other.max)

        return Interval(new_min, new_max)


    def __and__(self, other: "Interval") -> "Interval":
        # bottom & x = bottom
        if self.min is not None and self.max is not None and self.min > self.max:
            return self

        if other.min is not None and other.max is not None and other.min > other.max:
            return other

        # Lower bound: choose the largest
        if self.min is None:
            new_min = other.min
        elif other.min is None:
            new_min = self.min
        else:
            new_min = max(self.min, other.min)

        # Upper bound: choose the smallest
        if self.max is None:
            new_max = other.max
        elif other.max is None:
            new_max = self.max
        else:
            new_max = min(self.max, other.max)

        # Empty intersection = bottom
        if new_min is not None and new_max is not None and new_min > new_max:
            return Interval(1, 0)

        return Interval(new_min, new_max)


    def __lt__(self, other: "Interval") -> bool:
        # bottom is below every non-bottom interval
        self_bottom = (
            self.min is not None
            and self.max is not None
            and self.min > self.max
        )

        other_bottom = (
            other.min is not None
            and other.max is not None
            and other.min > other.max
        )

        if self_bottom:
            return not other_bottom

        if other_bottom:
            return False

        # self <= other means self is contained in other
        lower_ok = (
            other.min is None
            or (self.min is not None and self.min >= other.min)
        )

        upper_ok = (
            other.max is None
            or (self.max is not None and self.max <= other.max)
        )

        return lower_ok and upper_ok and self != other

    def __gt__(self, other: "Interval") -> bool:
        return other < self

    def arithmetic(
        self, other: "Interval", opr: jvm.BinaryOpr
    ) -> tuple["Interval", set[str]]:
        match opr:
            case jvm.BinaryOpr.Add:
                if self.min is not None and self.max is not None and self.min > self.max:
                    return (Interval(1, 0), set())

                if other.min is not None and other.max is not None and other.min > other.max:
                    return (Interval(1, 0), set())

                new_min = (
                    None
                    if self.min is None or other.min is None
                    else self.min + other.min
                )

                new_max = (
                    None
                    if self.max is None or other.max is None
                    else self.max + other.max
                )

                return (Interval(new_min, new_max), set())

            case jvm.BinaryOpr.Sub:
                if self.min is not None and self.max is not None and self.min > self.max:
                    return (Interval(1, 0), set())

                if other.min is not None and other.max is not None and other.min > other.max:
                    return (Interval(1, 0), set())

                new_min = (
                    None
                    if self.min is None or other.max is None
                    else self.min - other.max
                )

                new_max = (
                    None
                    if self.max is None or other.min is None
                    else self.max - other.min
                )

                return (Interval(new_min, new_max), set())

            case jvm.BinaryOpr.Mul:
                if self.min is not None and self.max is not None and self.min > self.max:
                    return (Interval(1, 0), set())

                if other.min is not None and other.max is not None and other.min > other.max:
                    return (Interval(1, 0), set())

                # If one interval is exactly zero
                if self.min == 0 and self.max == 0:
                    return (Interval(0, 0), set())

                if other.min == 0 and other.max == 0:
                    return (Interval(0, 0), set())

                # Conservative result for unbounded intervals
                if (
                    self.min is None
                    or self.max is None
                    or other.min is None
                    or other.max is None
                ):
                    return (Interval.top(), set())

                values = [
                    self.min * other.min,
                    self.min * other.max,
                    self.max * other.min,
                    self.max * other.max,
                ]

                return (Interval(min(values), max(values)), set())

            case jvm.BinaryOpr.Div:
                if self.min is not None and self.max is not None and self.min > self.max:
                    return (Interval(1, 0), set())

                if other.min is not None and other.max is not None and other.min > other.max:
                    return (Interval(1, 0), set())

                errors = set()

                # divisor may contain zero
                if other.min is None or other.min <= 0:
                    if other.max is None or other.max >= 0:
                        errors.add("divide by zero")

                # Keep division conservative when bounds are infinite
                # or the divisor interval contains zero
                if (
                    self.min is None
                    or self.max is None
                    or other.min is None
                    or other.max is None
                    or (other.min <= 0 <= other.max)
                ):
                    return (Interval.top(), errors)

                def trunc_div(a: int, b: int) -> int:
                    result = abs(a) // abs(b)
                    return result if (a >= 0) == (b >= 0) else -result

                values = [
                    trunc_div(self.min, other.min),
                    trunc_div(self.min, other.max),
                    trunc_div(self.max, other.min),
                    trunc_div(self.max, other.max),
                ]

                return (Interval(min(values), max(values)), errors)

            case _:
                raise NotImplementedError(f"TODO: {opr}")