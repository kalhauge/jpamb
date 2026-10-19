import sys
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

from abstractions import SignSet

import jpamb
from jvm import state
import sexpr
from jpamb import jvm
from jvm.state import PC, StackInt

@dataclass(frozen=True)
class AbstractReference(sexpr.AsSExpr):
    pcs: frozenset[PC] 

    def __or__(self, other):
        return AbstractReference(self.pcs | other.pcs)

    def __and__(self, other):
        return AbstractReference(self.pcs & other.pcs)

    def __le__(self, other):
        return self.pcs.issubset(other.pcs)

    def __iter__(self):
        return iter(self.pcs)

    def __str__(self):
        return f"Ref({{{', '.join(map(str, self.pcs))}}})"

    def __sexpr__(self):
            return sexpr.data("abstract-reference", *self.pcs)
    
    

@dataclass(frozen=True)
class StackValue(sexpr.AsSExpr):
    inner_value: SignSet | AbstractReference

    def __or__(self, other):
        assert isinstance(other, StackValue)
        
        if type(self.inner_value) is type(other.inner_value):
            return StackValue(self.inner_value | other.inner_value)
            
        if isinstance(self.inner_value, SignSet) and self.inner_value == SignSet.bot(): 
            return other
        if isinstance(other.inner_value, SignSet) and other.inner_value == SignSet.bot(): 
            return self
            
        return StackValue(SignSet.top())

    def __and__(self, other):
        assert isinstance(other, StackValue)
        
        if type(self.inner_value) is type(other.inner_value):
            return StackValue(self.inner_value & other.inner_value)
            
        return StackValue(SignSet.bot())

    def __le__(self, other):
        assert isinstance(other, StackValue)
        
        if type(self.inner_value) is type(other.inner_value):
            return self.inner_value <= other.inner_value
            
        if isinstance(self.inner_value, SignSet) and self.inner_value == SignSet.bot():
            return True
        if isinstance(other.inner_value, SignSet) and other.inner_value == SignSet.top():
            return True
            
        return False

    def __sexpr__(self):
        return self.inner_value.__sexpr__()
        
@dataclass(frozen=True)
class State(sexpr.AsSExpr):
    locals: tuple[StackValue, ...]
    stack: tuple[StackValue, ...]
    heap: dict[PC, StackValue]  

    def __post_init__(self):
        assert isinstance(self.locals, tuple)
        assert isinstance(self.stack, tuple)
        assert isinstance(self.heap, dict)

    def __str__(self):
        heap_str = ", ".join(f"{k}: {v}" for k, v in self.heap.items())
        return f"{', '.join(map(str, self.locals))}/{':'.join(map(str, self.stack))}/{{{heap_str}}}"

    def __or__(self, other):
        assert isinstance(other, State), f"Expected State but got {other!r}"
        assert len(self.stack) == len(other.stack), "Stacks should be equal length"
        assert len(self.locals) == len(other.locals), "Locals should be equal length"

        new_heap = self.heap.copy()
        for k, v in other.heap.items():
            if k in new_heap:
                new_heap[k] = new_heap[k] | v
            else:
                new_heap[k] = v

        return State(
            tuple(s1 | s2 for s1, s2 in zip(self.locals, other.locals)),
            tuple(s1 | s2 for s1, s2 in zip(self.stack, other.stack)),
            new_heap
        )
    
    def push(self, value: StackValue):
        assert isinstance(value, StackValue), f"Expected StackValue, got {type(value)}"
        return State(self.locals, self.stack + (value,), self.heap)

    def pop(self, number=1):
        return self.stack[-number:], State(self.locals, self.stack[:-number], self.heap)

    def load(self, index):
        return self.locals[index]

    def store(self, index, value: StackValue):
        return State(
            tuple(self.locals[:index]) + (value,) + tuple(self.locals[index + 1:]),
            self.stack,
            self.heap
        )

    def save_heap(self, abstract_reference: AbstractReference, value: StackValue):
        new_heap = self.heap.copy()
        for key in abstract_reference:
            current = new_heap.get(key, StackValue(SignSet.bot()))
            new_heap[key] = current | value
            
        return State(
            self.locals,
            self.stack,
            new_heap,
        )

    def load_heap(self, abstract_reference: AbstractReference):
        res = StackValue(SignSet.bot())
        for key in abstract_reference:
            res = res | self.heap.get(key, StackValue(SignSet.bot()))
        return res

    @classmethod
    def abstract(cls, locals_values, stack_values, heap_values):
        locals_t = tuple(StackValue(SignSet.abstract(vs)) for vs in locals_values)
        stack_t = tuple(StackValue(SignSet.abstract(vs)) for vs in stack_values)
        heap_d = {key: StackValue(SignSet.abstract(vs)) for key, vs in heap_values.items()}

        return cls(locals_t, stack_t, heap_d)

    def __le__(self, other):
        assert isinstance(other, State), f"Expected State but got {other!r}"
        assert len(self.stack) == len(other.stack), "Stacks should be equal length"
        assert len(self.locals) == len(other.locals), "Locals should be equal length"

        return (
            all(s1 <= s2 for s1, s2 in zip(self.locals, other.locals))
            and all(s1 <= s2 for s1, s2 in zip(self.stack, other.stack))
            and all(k in other.heap and v <= other.heap[k] for k, v in self.heap.items())
        )

    def __and__(self, other):
        assert isinstance(other, State), f"Expected State but got {other!r}"
        assert len(self.stack) == len(other.stack), "Stacks should be equal length"
        assert len(self.locals) == len(other.locals), "Locals should be equal length"

        new_heap = {}
        for k in self.heap:
            if k in other.heap:
                new_heap[k] = self.heap[k] & other.heap[k]

        return State(
            tuple(s1 & s2 for s1, s2 in zip(self.locals, other.locals)),
            tuple(s1 & s2 for s1, s2 in zip(self.stack, other.stack)),
            new_heap
        )

def manystep(
    bc: jpamb.Bytecode,
    pc: PC,
    state: State,
) -> Iterable[tuple[PC, object] | str]:
    opr = bc[pc]
    # with open("my_debug.log", "a", encoding="utf-8") as log_file:
    #     log_file.write(f"[DEBUG] PC: {pc.offset:03d} | Instr: {opr}\n")
    #     log_file.write(f"        State: {state}\n")
    match opr:
        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            va = StackValue(SignSet.abstract([StackInt(0)]))

            yield (pc + 1, state.push(va))

        case jvm.Ifz(condition=op, target=target):
            [val_wrapper], after = state.pop(1)

            for res in SignSet.compare(val_wrapper.inner_value, SignSet.abstract([StackInt(0)]), op):
                match res:
                    case True:
                        yield (pc % target, after)
                    case False:
                        yield (pc + 1, after)
                    case err:
                        yield err
                        
        case jvm.If(condition=op, target=target):
            [v1_wrapper, v2_wrapper], after = state.pop(2)
            for res in SignSet.compare(v1_wrapper.inner_value, v2_wrapper.inner_value, op):
                match res:
                    case True:
                        yield (pc % target, after)
                    case False:
                        yield (pc + 1, after)
                        
        case jvm.Push(type=jvm.Int(), value=value):
            va = StackValue(SignSet.abstract([StackInt(value)]))
            yield (pc + 1, state.push(va))

        case jvm.Push(type=jvm.Reference(), value=value):
            va = StackValue(SignSet(frozenset({0})))  # mock value, needs to be discarded when popping from the stack
            yield (pc + 1, state.push(va))

        case jvm.Load(index=i):
            va = state.load(i)
            yield (pc + 1, state.push(va))

        case jvm.Cast():
            [value], after = state.pop(1)
            yield (pc + 1, after.push(value))
        
        case jvm.Store(index=i):
            [value], after = state.pop(1)
            yield (pc + 1, after.store(i, value))

        case jvm.Goto(target=t):
            yield (pc % t, state)

        case jvm.Binary(operant=op):
            [v1_wrapper, v2_wrapper], after = state.pop(2)

            result, errors = SignSet.arithmetic(v1_wrapper.inner_value, v2_wrapper.inner_value, op)

            yield (pc + 1, after.push(StackValue(result)))

            for error in errors:
                yield error

        case jvm.Return(type=None):
            yield "ok"

        case jvm.Return(type=t):
            # Hack -- we assume that we always return.
            yield "ok"

        case jvm.New(classname=jvm.ClassName("java.lang.AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            yield "assertion error"

        case jvm.NewArray(type=t):
            [size_wrapper], after = state.pop()
            size = size_wrapper.inner_value
            
            if -1 in size:
                yield "negative array size"
            
            if 0 in size or 1 in size:
                ref = AbstractReference(frozenset({pc}))
                yield (pc + 1, after.push(StackValue(ref)).save_heap(ref, StackValue(SignSet(frozenset({0})))))
                
        case jvm.ArrayStore(type=t):
            [ref_wrapper, index_wrapper, val_wrapper], after = state.pop(3)
            
            index = index_wrapper.inner_value
            ref = ref_wrapper.inner_value
            
            if -1 in index:
                yield "out of bounds"
                
            if not isinstance(ref, AbstractReference):
                yield "null pointer"
            
            if (0 in index or 1 in index) and isinstance(ref, AbstractReference):
                yield (pc + 1, after.save_heap(ref, val_wrapper))
                yield "out of bounds"


        case jvm.ArrayLoad(type=t):
            [ref_wrapper, index_wrapper], after = state.pop(2)

            index = index_wrapper.inner_value
            ref = ref_wrapper.inner_value

            if -1 in index:
                yield "out of bounds"
                
            if 0 in index or 1 in index:
                yield "out of bounds"
                
            if not isinstance(ref, AbstractReference):
                yield "null pointer"

            if (0 in index or 1 in index) and isinstance(ref, AbstractReference):
                val = after.load_heap(ref)
                yield (pc + 1, after.push(val))

        case jvm.Dup():
            [v1], after = state.pop(1)
            yield (pc + 1, after.push(v1).push(v1))

        case jvm.ArrayLength():
            [ref_wrapper], after = state.pop(1)
            ref = ref_wrapper.inner_value

            if not isinstance(ref, AbstractReference):
                yield "null pointer"
            yield (pc+1, after.push(StackValue(SignSet(frozenset({0, 1})))))

        case jvm.Incr(index=i, amount=a):
            current_val_wrapper = state.load(i)
            current_val = current_val_wrapper.inner_value
            
            if a > 0:
                a_sign = frozenset({1})
            elif a < 0:
                a_sign = frozenset({-1})
            else:
                a_sign = frozenset({0})

            result, errors = SignSet.arithmetic(current_val, SignSet(a_sign), jvm.BinaryOpr.Add)
            yield (pc+1, state.store(i, StackValue(result)))
            for error in errors:
                yield error

        case a:
            raise NotImplementedError(f"Unsupported operation {a.help()}")


def initialstate(
    bc: jpamb.Bytecode,
    methodid: jvm.AbsMethodID,
    inputs: jpamb.Input | None,
) -> dict[PC, State]:
    method = bc.getmethod(methodid)
    locals = [StackValue(SignSet.bot())] * method.max_locals
    heap = {}

    if inputs is None:
        for i, p in enumerate(methodid.extension.params):
            match p:
                case jvm.Array() | jvm.Reference():
                    dummy_pc = PC(methodid, -(i + 1))
                    locals[i] = StackValue(AbstractReference(frozenset({dummy_pc})))
                    heap[dummy_pc] = StackValue(SignSet.top())
                case _:
                    locals[i] = StackValue(SignSet.top())
    else:
        for i, x in enumerate(inputs.values):
            match x:
                case jpamb.case.Boolean(value=value):
                    locals[i] = StackValue(SignSet.abstract([StackInt(int(value))]))
                case jpamb.case.Int(value=value):
                    locals[i] = StackValue(SignSet.abstract([StackInt(int(value))]))
                case jpamb.case.Array():
                    dummy_pc = PC(methodid, -(i + 1))
                    locals[i] = StackValue(AbstractReference(frozenset({dummy_pc})))
                    heap[dummy_pc] = StackValue(SignSet.top())
                case _:
                    raise NotImplementedError(f"Unsupported value {x!r}")

    state = State(tuple(locals), (), heap)
    return {PC(methodid, 0): state}


@dataclass
class AbstractInterpreter:
    bc: jpamb.Bytecode
    worklist: deque[PC]
    states: dict[PC, State]

    @staticmethod
    def initial(bc: jpamb.Bytecode, methodid: jvm.AbsMethodID, inputs):
        states = initialstate(bc, methodid, inputs)
        worklist = deque(states.keys())

        return AbstractInterpreter(bc, worklist, states)

    def step(self) -> tuple[PC, set[str]]:
        pc = self.worklist.pop()

        # print(f"Stepping {pc}:\n > {self.bc[pc]}", file=sys.stderr)

        finals = set()
        try:
            results = manystep(self.bc, pc, self.states[pc])
            for res in results:
                if isinstance(res, str):
                    finals.add(res)
                else:
                    pc_, st = res

                    before = self.states.get(pc_, None)
                    if before is None:
                        after = st
                    else:
                        after = before | st
                    if before is None or after != before:
                        self.states[pc_] = after
                        self.worklist.append(pc_)
        except Exception as e:
            # with open("my_debug1.log", "a", encoding="utf-8") as log_file:
            #     log_file.write(f"[DEBUG], Error: {e}\n")
            raise e

        return pc, finals


def interpret():
    """The static analysis"""
    methodid, input, steps = jpamb.getcase(
        "static",
        "1.0",
        "best analyzers",
        ["static", "python"],
        for_science=True,
    )
    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    ai = AbstractInterpreter.initial(bc, methodid, input)

    x = jpamb.emit_init(ai.states)

    finals_seen = set()
    while steps > 0 and ai.worklist:
        pc, final = ai.step()

        finals_seen |= final

        for f in final:
            jpamb.emit_step(x, pc, f, depth=3)
            steps -= 1

        x = jpamb.emit_step(x, pc, ai.states, depth=3)
        steps -= 1

    # The worklist reached a fixpoint without finding a terminating state
    if not ai.worklist and not finals_seen:
        jpamb.emit_step(x, pc, "*", depth=3)


def analyse():
    """The static analysis"""

    methodid = jpamb.getmethodid(
        "static",
        "1.0",
        "best analyzers",
        ["static", "python"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    steps = 300

    ai = AbstractInterpreter.initial(bc, methodid, None)

    final = set()
    while steps > 0 and ai.worklist:
        _pc, finals = ai.step()
        final |= finals
        steps -= 1

    if not ai.worklist and not final:
        final.add("*")

    for f in jpamb.QUERIES:
        if f not in final:
            print(f"{f};no")
        else:
            print(f"{f};maybe")