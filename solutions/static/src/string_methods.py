"""String references and the small library model used by the static interpreter.

Only string objects are supported. Object IDs describe parameters or interned
literals, not concrete JVM addresses. Contents and nullability stay separate.
"""

from dataclasses import dataclass

from abstractions import StringSet

import jvm
import sexpr


@dataclass(frozen=True)
class AbstractReference:
    targets: frozenset[str]
    may_be_null: bool = False

    def __or__(self, other):
        if not isinstance(other, AbstractReference):
            raise NotImplementedError("Cannot join a reference and an integer")
        return AbstractReference(
            self.targets | other.targets, self.may_be_null or other.may_be_null
        )

    def __sexpr__(self):
        return sexpr.sexpr(["reference", sorted(self.targets), self.may_be_null])

    def compare(self, other, operation):
        """Reference identity, never string-content equality.

        Parameter locations summarize objects, so overlap does not prove identity.
        Even disjoint parameter locations may alias. Only distinct literals are
        known to be different objects (Java interns string constants).
        """
        if not isinstance(other, AbstractReference):
            raise NotImplementedError("Reference comparison requires references")
        if operation not in (jvm.CmpOpr.Eq, jvm.CmpOpr.Ne):
            raise NotImplementedError("Unsupported reference comparison")
        answers = set()
        if self.may_be_null and other.may_be_null:
            answers.add(True)
        if (self.may_be_null and other.targets) or (self.targets and other.may_be_null):
            answers.add(False)
        for left in self.targets:
            for right in other.targets:
                if left.startswith("literal:") and right.startswith("literal:"):
                    answers.add(left == right)
                else:
                    answers.update({True, False})
        return answers if operation == jvm.CmpOpr.Eq else {not a for a in answers}


def contents(reference, heap):
    """Join contents from every possible non-null target."""
    if not isinstance(reference, AbstractReference):
        raise NotImplementedError("Expected a string reference")
    result = StringSet.bot()
    for target in reference.targets:
        result = result | heap[target]
    return result


def equals(receiver, argument, heap):
    """Return boolean possibilities and exceptions for String.equals(Object)."""
    left = contents(receiver, heap)
    right = contents(argument, heap)
    errors = {"null pointer"} if receiver.may_be_null else set()
    answers = left.equals(right)
    if receiver.targets and argument.may_be_null:
        answers.add(False)
    return answers, errors
