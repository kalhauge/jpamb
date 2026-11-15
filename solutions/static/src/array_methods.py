"""One-dimensional int/char arrays with a single summary of all elements.

Lengths and contents use the selected integer domain. We never enumerate array
positions. Writes are weak (join with previous contents), which safely handles
unknown indices, aliases, and repeated allocations at one bytecode site.
"""

from dataclasses import dataclass, replace

from abstractions import I32_MAX, IntegerAbstraction
from string_methods import AbstractReference

import jvm
import sexpr
from jvm.state import StackInt


def int_range(domain, lower, upper):
    """Abstract an inclusive range in signs, intervals, or their product.

    Endpoints determine interval bounds; zero must also be included for signs
    when the range crosses zero. This never adds a hidden interval domain.
    """
    values = [StackInt(lower), StackInt(upper)]
    if lower <= 0 <= upper:
        values.append(StackInt(0))
    return domain.abstract(values)


def check_type(element_type):
    if not isinstance(element_type, (jvm.Int, jvm.Char)):
        raise NotImplementedError(f"Unsupported array element type: {element_type}")


@dataclass(frozen=True)
class AbstractArray:
    element_type: jvm.Type
    length: IntegerAbstraction
    elements: IntegerAbstraction

    def __or__(self, other):
        if (
            not isinstance(other, AbstractArray)
            or self.element_type != other.element_type
        ):
            raise NotImplementedError("Cannot join incompatible heap objects")
        return AbstractArray(
            self.element_type,
            self.length | other.length,
            self.elements | other.elements,
        )

    def widen(self, newer):
        domain = type(self.length)
        # Lengths stay nonnegative even if widening expands their bounds.
        length = self.length.widen(newer.length) & int_range(domain, 0, I32_MAX)
        elements = self.elements.widen(newer.elements)
        if isinstance(self.element_type, jvm.Char):
            elements = elements & int_range(domain, 0, 65535)
        return AbstractArray(self.element_type, length, elements)

    def __sexpr__(self):
        return sexpr.sexpr(["array", self.element_type, self.length, self.elements])


def allocate(element_type, length, domain):
    check_type(element_type)
    if length == domain.bot():
        return None
    zero = domain.abstract([StackInt(0)])
    if True in length.compare(zero, jvm.CmpOpr.Lt):
        # JPAMB has no negative-array-size outcome. Do not mislabel this as an
        # index error or silently discard it: leave analysis incomplete instead.
        raise NotImplementedError("Possible negative array size is not modeled")
    elements = zero if True in length.compare(zero, jvm.CmpOpr.Gt) else domain.bot()
    return AbstractArray(element_type, length, elements)


def parameter(element_type, supplied, domain):
    """Unknown inputs may be empty; supplied inputs retain their abstract length."""
    check_type(element_type)
    if supplied is None:
        elements = (
            int_range(domain, 0, 65535)
            if isinstance(element_type, jvm.Char)
            else domain.top()
        )
        return AbstractArray(element_type, int_range(domain, 0, I32_MAX), elements)
    if supplied.contains != element_type:
        raise NotImplementedError("Array input type does not match parameter")
    values = []
    for value in supplied.values:
        if isinstance(element_type, jvm.Char):
            if not isinstance(value, str) or len(value) != 1 or ord(value) > 65535:
                raise NotImplementedError("Expected a single Java UTF-16 char")
            value = ord(value)
        values.append(StackInt(value))
    length = domain.abstract([StackInt(len(values))])
    return AbstractArray(element_type, length, domain.abstract(values))


def targets(reference, heap):
    if not isinstance(reference, AbstractReference):
        raise NotImplementedError("Expected an array reference")
    result = []
    for target in sorted(reference.targets):
        array = heap[target]
        if not isinstance(array, AbstractArray):
            raise NotImplementedError("Expected an array heap object")
        result.append((target, array))
    return result


def length(reference, heap, domain):
    result = domain.bot()
    arrays = targets(reference, heap)
    for _, array in arrays:
        result = result | array.length
    errors = {"null pointer"} if reference.may_be_null else set()
    return result, errors


def access(reference, index, heap, domain, element_type):
    """Return possible valid targets and errors, including both when uncertain."""
    check_type(element_type)
    arrays = targets(reference, heap)
    if index == domain.bot():
        return [], set()
    errors = {"null pointer"} if reference.may_be_null else set()
    valid = []
    zero = domain.abstract([StackInt(0)])
    nonnegative_index = index & int_range(domain, 0, I32_MAX)
    for target, array in arrays:
        if array.element_type != element_type:
            raise NotImplementedError("Array instruction and element types differ")
        if True in index.compare(zero, jvm.CmpOpr.Lt) or True in index.compare(
            array.length, jvm.CmpOpr.Ge
        ):
            errors.add("out of bounds")
        if nonnegative_index != domain.bot() and True in nonnegative_index.compare(
            array.length, jvm.CmpOpr.Lt
        ):
            valid.append((target, array))
    return valid, errors


def load(reference, index, heap, domain, element_type):
    valid, errors = access(reference, index, heap, domain, element_type)
    result = domain.bot()
    for _, array in valid:
        result = result | array.elements
    return result, errors


def store(reference, index, value, heap, domain, element_type):
    if value == domain.bot():
        return None, set()
    valid, errors = access(reference, index, heap, domain, element_type)
    if not valid:
        return None, errors
    if isinstance(element_type, jvm.Char):
        # castore truncates to unsigned 16 bits. Keep already-in-range values;
        # otherwise cover every possible char instead of using signed int data.
        zero = domain.abstract([StackInt(0)])
        maximum = domain.abstract([StackInt(65535)])
        if value.compare(zero, jvm.CmpOpr.Ge) != {True} or value.compare(
            maximum, jvm.CmpOpr.Le
        ) != {True}:
            value = int_range(domain, 0, 65535)
    updated = dict(heap)
    for target, array in valid:
        updated[target] = replace(array, elements=array.elements | value)
    return updated, errors
