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
    alpha_a = b.abstract(a)

    for value in a:
        assert value in alpha_a, f"{value} not in {a}"

    if alpha_a <= b:
        for value in a:
            assert value in b, f"{value} not in {b}"


type Sign = Literal[-1, 0, 1]


def to_sign(value: jvms.StackValue) -> Sign:
    match value:
        case jvms.StackInt(v):
            return (v > 0) - (v < 0)
        case a:
            raise NotImplementedError(f"Unsupported value {value!r}")


class IntegerAbstraction(Abstraction, Lattice):
    """Operations the bytecode interpreter needs from an integer domain."""

    @abstractmethod
    def arithmetic(self, other, opr): ...

    @abstractmethod
    def compare(self, other, opr): ...

    def widen(self, newer):
        """Finite domains such as signs need only their ordinary join."""
        return self | newer


@dataclass(frozen=True)
class SignSet(IntegerAbstraction):
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
    def top(cls) -> Self:
        return cls(frozenset([-1, 0, 1]))

    def __or__(self, other: "SignSet") -> "SignSet":
        if not isinstance(other, SignSet):
            return NotImplemented

        return SignSet(self.signs | other.signs)

    def __and__(self, other: "SignSet") -> "SignSet":
        if not isinstance(other, SignSet):
            return NotImplemented

        return SignSet(self.signs & other.signs)

    # Ordering describes inclusion of possibilities, not numeric magnitude.
    def __lt__(self, other: "SignSet") -> bool:
        if not isinstance(other, SignSet):
            return NotImplemented
        return self.signs < other.signs

    def __gt__(self, other: "SignSet") -> bool:
        if not isinstance(other, SignSet):
            return NotImplemented
        return self.signs > other.signs

    def arithmetic(
        self, other: "SignSet", opr: jvm.BinaryOpr
    ) -> tuple["SignSet", set[str]]:
        output = set()
        errors = set()

        # Each pair represents all Java integers with those two signs.
        # Empty operands produce no pairs, so their result stays empty.
        for left in self.signs:
            for right in other.signs:
                match opr:
                    case jvm.BinaryOpr.Add:
                        if left == 0:
                            output.add(right)
                        elif right == 0:
                            output.add(left)
                        else:
                            # Overflow prevents assuming that equal signs stay equal.
                            output.update([-1, 0, 1])

                    case jvm.BinaryOpr.Sub:
                        if right == 0:
                            output.add(left)
                        elif left == 0:
                            output.add(-right)
                            if right == -1:
                                # Negating Integer.MIN_VALUE still gives a negative.
                                output.add(-1)
                        else:
                            output.update([-1, 0, 1])

                    case jvm.BinaryOpr.Mul:
                        if left == 0 or right == 0:
                            output.add(0)
                        else:
                            # Multiplication may overflow to any sign, including zero.
                            output.update([-1, 0, 1])

                    case jvm.BinaryOpr.Div:
                        if right == 0:
                            errors.add("divide by zero")
                        elif left == 0:
                            output.add(0)
                        else:
                            # Java truncates towards zero: 1 / 2 is zero.
                            output.add(0)
                            output.add(left * right)
                            if left == -1 and right == -1:
                                # Integer.MIN_VALUE / -1 overflows to Integer.MIN_VALUE.
                                output.add(-1)

                    case jvm.BinaryOpr.Rem:
                        if right == 0:
                            errors.add("divide by zero")
                        else:
                            # A nonzero remainder has the dividend's sign.
                            output.add(0)
                            output.add(left)

                    case _:
                        raise NotImplementedError(f"Unsupported arithmetic: {opr}")

        return SignSet(frozenset(output)), errors

    def compare(self, other: "SignSet", opr: jvm.CmpOpr) -> Iterable[bool]:
        cases = set()
        for left in self.signs:
            for right in other.signs:
                # Two positive (or two negative) values may be equal or differ
                # in either direction. Signs alone cannot decide the comparison.
                if left == right and left != 0:
                    cases.update([True, False])
                    continue

                # Different signs, or two zeros, determine the answer exactly.
                match opr:
                    case jvm.CmpOpr.Eq:
                        cases.add(left == right)
                    case jvm.CmpOpr.Ne:
                        cases.add(left != right)
                    case jvm.CmpOpr.Lt:
                        cases.add(left < right)
                    case jvm.CmpOpr.Le:
                        cases.add(left <= right)
                    case jvm.CmpOpr.Gt:
                        cases.add(left > right)
                    case jvm.CmpOpr.Ge:
                        cases.add(left >= right)
                    case _:
                        raise NotImplementedError(f"Unsupported comparison: {opr}")
        return cases


I32_MIN = -(2**31)
I32_MAX = 2**31 - 1


def java_quotient(left: int, right: int) -> int:
    """Integer division truncated toward zero, without floating-point rounding.

    Return the mathematical quotient; the caller handles Java int overflow.
    """
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


@dataclass(frozen=True)
class Interval(IntegerAbstraction):
    """Inclusive Java int bounds. [1, 0] is the unique empty interval.

    Top uses the Java limits instead of infinities. If arithmetic may overflow,
    use top, except that singleton operations can be wrapped exactly.
    """

    min: int
    max: int

    def __post_init__(self):
        if self.min > self.max:
            object.__setattr__(self, "min", 1)
            object.__setattr__(self, "max", 0)
        elif self.min < I32_MIN or self.max > I32_MAX:
            raise ValueError("Interval bounds must be Java int values")

    def __str__(self):
        return "bottom" if self.is_bottom() else f"{self.min}:{self.max}"

    def __sexpr__(self):
        return str(self)

    def is_bottom(self):
        return self.min > self.max

    @classmethod
    def abstract(cls, values: Iterable[jvms.StackValue]) -> Self:
        numbers = []
        for value in values:
            if not isinstance(value, jvms.StackInt):
                raise NotImplementedError("Expected an integer")
            numbers.append(value.value)
        return cls(min(numbers), max(numbers)) if numbers else cls.bot()

    @classmethod
    def top(cls) -> Self:
        return cls(I32_MIN, I32_MAX)

    @classmethod
    def bot(cls) -> Self:
        return cls(1, 0)

    def __contains__(self, value):
        if not isinstance(value, jvms.StackInt):
            raise NotImplementedError("Expected an integer")
        return self.min <= value.value <= self.max

    def __lt__(self, other):
        if self.is_bottom():
            return not other.is_bottom()
        return (
            not other.is_bottom()
            and self != other
            and other.min <= self.min
            and self.max <= other.max
        )

    def __gt__(self, other):
        return other < self

    def __or__(self, other):
        if self.is_bottom():
            return other
        if other.is_bottom():
            return self
        return Interval(min(self.min, other.min), max(self.max, other.max))

    def __and__(self, other):
        if self.is_bottom() or other.is_bottom():
            return self.bot()
        return Interval(max(self.min, other.min), min(self.max, other.max))

    def widen(self, newer):
        """Jump an expanding bound to a Java limit so loops stabilize quickly."""
        if self.is_bottom():
            return newer
        if newer.is_bottom():
            return self
        return Interval(
            I32_MIN if newer.min < self.min else self.min,
            I32_MAX if newer.max > self.max else self.max,
        )

    @classmethod
    def bounded(cls, lower, upper):
        """Cover possible wrapping conservatively; preserve exact constants."""
        if lower == upper:
            wrapped = (lower - I32_MIN) % (2**32) + I32_MIN
            return cls(wrapped, wrapped)
        if lower < I32_MIN or upper > I32_MAX:
            return cls.top()
        return cls(lower, upper)

    def arithmetic(self, other, opr):
        if self.is_bottom() or other.is_bottom():
            return self.bot(), set()

        match opr:
            case jvm.BinaryOpr.Add:
                result = self.bounded(self.min + other.min, self.max + other.max)
            case jvm.BinaryOpr.Sub:
                result = self.bounded(self.min - other.max, self.max - other.min)
            case jvm.BinaryOpr.Mul:
                products = [
                    a * b for a in (self.min, self.max) for b in (other.min, other.max)
                ]
                result = self.bounded(min(products), max(products))
            case jvm.BinaryOpr.Div | jvm.BinaryOpr.Rem:
                errors = {"divide by zero"} if jvms.StackInt(0) in other else set()
                result = self.bot()
                # Remove zero from normal execution. Negative and positive
                # divisors are evaluated separately, then their results joined.
                for part in (
                    other & Interval(I32_MIN, -1),
                    other & Interval(1, I32_MAX),
                ):
                    if not part.is_bottom():
                        result = result | self.divide_nonzero(part, opr)
                return result, errors
            case _:
                raise NotImplementedError(f"Unsupported arithmetic: {opr}")
        return result, set()

    def divide_nonzero(self, divisor, opr):
        """The divisor must lie wholly above or below zero."""
        if self.min == self.max and divisor.min == divisor.max:
            quotient = java_quotient(self.min, divisor.min)
            value = (
                quotient
                if opr == jvm.BinaryOpr.Div
                else self.min - quotient * divisor.min
            )
            return self.bounded(value, value)

        if opr == jvm.BinaryOpr.Div:
            # MIN_VALUE / -1 wraps; mixed ranges containing this pair use top.
            if self.min == I32_MIN and jvms.StackInt(-1) in divisor:
                return self.top()
            quotients = [
                java_quotient(a, b)
                for a in (self.min, self.max)
                for b in (divisor.min, divisor.max)
            ]
            return Interval(min(quotients), max(quotients))

        # A remainder has the dividend's sign and magnitude < |divisor|.
        limit = max(abs(divisor.min), abs(divisor.max)) - 1
        lower = max(self.min, -limit) if self.min < 0 else 0
        upper = min(self.max, limit) if self.max > 0 else 0
        return Interval(lower, upper)

    def compare(self, other, opr):
        if self.is_bottom() or other.is_bottom():
            return set()
        match opr:
            case jvm.CmpOpr.Eq:
                if (self & other).is_bottom():
                    return {False}
                if self.min == self.max == other.min == other.max:
                    return {True}
                return {False, True}
            case jvm.CmpOpr.Ne:
                return {not answer for answer in self.compare(other, jvm.CmpOpr.Eq)}
            case jvm.CmpOpr.Lt:
                if self.max < other.min:
                    return {True}
                if self.min >= other.max:
                    return {False}
            case jvm.CmpOpr.Le:
                if self.max <= other.min:
                    return {True}
                if self.min > other.max:
                    return {False}
            case jvm.CmpOpr.Gt:
                return other.compare(self, jvm.CmpOpr.Lt)
            case jvm.CmpOpr.Ge:
                return other.compare(self, jvm.CmpOpr.Le)
            case _:
                raise NotImplementedError(f"Unsupported comparison: {opr}")
        return {False, True}


SIGN_RANGES = {
    -1: Interval(I32_MIN, -1),
    0: Interval(0, 0),
    1: Interval(1, I32_MAX),
}


@dataclass(frozen=True)
class SignInterval(IntegerAbstraction):
    """One integer described by BOTH components, interpreted as intersection.

    Normalization removes impossible signs and trims the bounds. Operations split
    the interval by permitted signs, so an excluded zero is never reintroduced
    as an input. The representation can retain the hole at zero after a join.
    """

    signs: SignSet
    interval: Interval

    def __post_init__(self):
        parts = self.parts()
        interval = Interval.bot()
        for _, part in parts:
            interval = interval | part
        object.__setattr__(self, "signs", SignSet(frozenset(sign for sign, _ in parts)))
        object.__setattr__(self, "interval", interval)

    def parts(self):
        parts = []
        for sign in sorted(self.signs.signs):
            part = self.interval & SIGN_RANGES[sign]
            if not part.is_bottom():
                parts.append((sign, part))
        return parts

    @classmethod
    def abstract(cls, values) -> Self:
        values = list(values)  # Both components must see the same generator input.
        return cls(SignSet.abstract(values), Interval.abstract(values))

    @classmethod
    def top(cls) -> Self:
        return cls(SignSet.top(), Interval.top())

    @classmethod
    def bot(cls) -> Self:
        return cls(SignSet.bot(), Interval.bot())

    def __contains__(self, value):
        return value in self.signs and value in self.interval

    def __lt__(self, other):
        return (
            self != other
            and self.signs <= other.signs
            and self.interval <= other.interval
        )

    def __gt__(self, other):
        return other < self

    def __or__(self, other):
        return SignInterval(self.signs | other.signs, self.interval | other.interval)

    def __and__(self, other):
        return SignInterval(self.signs & other.signs, self.interval & other.interval)

    def widen(self, newer):
        return SignInterval(
            self.signs | newer.signs, self.interval.widen(newer.interval)
        )

    def arithmetic(self, other, opr):
        result = self.bot()
        errors = set()
        for left_sign, left in self.parts():
            for right_sign, right in other.parts():
                interval, interval_errors = left.arithmetic(right, opr)
                signs, sign_errors = SignSet(frozenset({left_sign})).arithmetic(
                    SignSet(frozenset({right_sign})), opr
                )
                result = result | SignInterval(signs, interval)
                # Both sound component summaries must allow an error for this
                # same pair of sign-restricted operands before we report it.
                errors |= interval_errors & sign_errors
        return result, errors

    def compare(self, other, opr):
        answers = set()
        for _, left in self.parts():
            for _, right in other.parts():
                answers |= left.compare(right, opr)
        return answers

    def __sexpr__(self):
        import sexpr

        return sexpr.sexpr(["sign-interval", self.signs, self.interval])


@dataclass(frozen=True)
class StringSet(Lattice):
    """At most eight exact contents, or None for any non-null string contents.

    The empty frozenset is bottom. Java null belongs to AbstractReference instead.
    This finite-height domain needs no widening: oversized joins become top.
    """

    values: frozenset[str] | None

    def __post_init__(self):
        if self.values is not None and len(self.values) > 8:
            object.__setattr__(self, "values", None)

    @classmethod
    def abstract(cls, values: Iterable[str]) -> Self:
        return cls(frozenset(values))

    @classmethod
    def top(cls) -> Self:
        return cls(None)

    def __contains__(self, value: str) -> bool:
        return self.values is None or value in self.values

    def __or__(self, other):
        if self.values is None or other.values is None:
            return self.top()
        return StringSet(self.values | other.values)

    def __and__(self, other):
        if self.values is None:
            return other
        if other.values is None:
            return self
        return StringSet(self.values & other.values)

    def __lt__(self, other):
        if self.values is None:
            return False
        return other.values is None or self.values < other.values

    def __gt__(self, other):
        return other < self

    def equals(self, other) -> set[bool]:
        """Possible content-equality answers; impossible operands give no answers."""
        if self == self.bot() or other == self.bot():
            return set()
        if self.values is None or other.values is None:
            return {True, False}
        return {left == right for left in self.values for right in other.values}

    def __sexpr__(self):
        import sexpr

        return sexpr.sexpr(
            ["strings", "top" if self.values is None else sorted(self.values)]
        )


@dataclass(frozen=True)
class BooleanSet:
    """Minimal JVM boolean support, independent of integer sign analysis.

    JVM booleans use 0 and 1 on the operand stack. Other integers and arithmetic
    are deliberately unsupported; this class is not a general integer domain.
    """

    values: frozenset[bool]

    @classmethod
    def abstract(cls, values):
        answers = set()
        for value in values:
            if not isinstance(value, jvms.StackInt) or value.value not in (0, 1):
                raise NotImplementedError(
                    "Integer values require sign or interval in --abstractions"
                )
            answers.add(bool(value.value))
        return cls(frozenset(answers))

    def __or__(self, other):
        return BooleanSet(self.values | other.values)

    def compare(self, other, operation):
        if not isinstance(other, BooleanSet):
            raise NotImplementedError("Boolean comparison requires boolean operands")
        comparisons = {
            jvm.CmpOpr.Eq: lambda a, b: a == b,
            jvm.CmpOpr.Ne: lambda a, b: a != b,
            jvm.CmpOpr.Lt: lambda a, b: a < b,
            jvm.CmpOpr.Le: lambda a, b: a <= b,
            jvm.CmpOpr.Gt: lambda a, b: a > b,
            jvm.CmpOpr.Ge: lambda a, b: a >= b,
        }
        return {comparisons[operation](a, b) for a in self.values for b in other.values}

    def __sexpr__(self):
        import sexpr

        return sexpr.sexpr(["booleans", sorted(self.values)])
