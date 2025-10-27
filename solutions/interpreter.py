import jpamb
from jpamb import jvm
from dataclasses import dataclass
from jpamb.jvm.base import MethodID
import sys
from loguru import logger
import random

logger.remove()
logger.add(sys.stderr, format="[{level}] {message}")

methodid, input = jpamb.getcase()


@dataclass
class PC:
    method: jvm.AbsMethodID
    offset: int

    def __iadd__(self, delta):
        self.offset += delta
        return self

    def __add__(self, delta):
        return PC(self.method, self.offset + delta)

    def __str__(self):
        return f"{self.method}:{self.offset}"


@dataclass
class Bytecode:
    suite: jpamb.Suite
    methods: dict[jvm.AbsMethodID, list[jvm.Opcode]]

    def __getitem__(self, pc: PC) -> jvm.Opcode:
        try:
            opcodes = self.methods[pc.method]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(pc.method))
            self.methods[pc.method] = opcodes

        return opcodes[pc.offset]


@dataclass
class Stack[T]:
    items: list[T]

    def __bool__(self) -> bool:
        return len(self.items) > 0

    @classmethod
    def empty(cls):
        return cls([])

    def peek(self) -> T:
        return self.items[-1]

    def pop(self) -> T:
        return self.items.pop(-1)

    def push(self, value):
        self.items.append(value)
        return self

    def __str__(self):
        if not self:
            return "ϵ"
        return "".join(f"{v}" for v in self.items)


suite = jpamb.Suite()
bc = Bytecode(suite, dict())


@dataclass
class Frame:
    locals: dict[int, jvm.Value]
    stack: Stack[jvm.Value]
    pc: PC

    def __str__(self):
        locals = ", ".join(f"{k}:{v}" for k, v in sorted(self.locals.items()))
        return f"<{{{locals}}}, {self.stack}, {self.pc}>"

    def from_method(method: jvm.AbsMethodID) -> "Frame":
        return Frame({}, Stack.empty(), PC(method, 0))


@dataclass
class State:
    heap: dict[int, jvm.Value]
    frames: Stack[Frame]

    def __str__(self):
        return f"{self.heap} {self.frames}"


def step(state: State) -> State | str:
    assert isinstance(state, State), f"expected frame but got {state}"
    frame = state.frames.peek()
    opr = bc[frame.pc]
    logger.debug(f"STEP {opr}\n{state}")
    match opr:
        case jvm.Push(value=v):
            #Positiver space: v must always be a JVM value:
            assert isinstance(v,jvm.Value), f"Expected JVM value, got {v!r}"
            frame.stack.push(v)
            frame.pc += 1
            return state
        
        case jvm.Load(type=jvm.Int(), index=i):
            frame.stack.push(frame.locals[i])
            frame.pc += 1
            return state
        
        case jvm.Dup():    # <--- NEW (dup)
            v = frame.stack.peek()
            #v must be a JVM Value (We didnt put the assertion at the start, bc v was not defined yet)
            assert isinstance(v,jvm.Value), f"Expected JVM value, got {v!r}"
            frame.stack.push(v)
            frame.pc += 1
            return state
        
        case jvm.Binary(type=jvm.Int(), operant=op):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"

            if op == jvm.BinaryOpr.Add:
                result = v1.value +v2.value
            elif op == jvm.BinaryOpr.Div:
                if v2.value!=0:
                    result = v1.value // v2.value
                else:
                     return "divide by zero"
            elif op == jvm.BinaryOpr.Mul:
                result =v1.value *v2.value 
            elif op == jvm.BinaryOpr.Rem:
                result = v1.value % v2.value
            elif op == jvm.BinaryOpr.Sub:
                result =v1.value -v2. value
            
            frame.stack.push(jvm.Value.int(result))
            frame.pc += 1

            return state
        


        case jvm.Return(type=t):
            #t is a type: None, jvm.Int(), jvm.Boolean(). It is not a null, int or boolean (these are the methods that it returns)
            #The return instruction can return a void or a value
            assert t is None or isinstance(t,jvm.Type), f"Expected JVM type or None, got a {t!r}"

            if t:
                v1 = frame.stack.pop()
                #The returned value must be a JVM Value
                assert isinstance(v1,jvm.Value), f"Expected JVM value, got a {v1!r}"

            state.frames.pop()
            if state.frames:
                frame = state.frames.peek()
                if t:
                    frame.stack.push(v1)
                frame.pc += 1
                return state
            else:
                return "ok"

                 
            
        case jvm.Get(field=field):
            assert field.extension.name == "$assertionsDisabled", f"should be $assertionsDisabled but was {field!r}"
            frame.stack.push(jvm.Value.int(0))
            frame.pc += 1
            return state


        case jvm.Ifz():
            v = frame.stack.pop()  #pop the top value from the stack
            assert isinstance(v,jvm.Value), f"Expected JVM value, got a {v!r}"
            
            cond = opr.condition
            assert cond in {"eq", "ne", "lt", "le", "gt", "ge"}, f"Unexpected condition {cond!r}"


            if cond == "ne":
                if v != jvm.Value.int(0):
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond =="eq":
                if v==jvm.Value.int(0):
                    frame.pc.offset = opr.target
                else:
                    frame.pc +=1
            if cond == "lt":
                if v < jvm.Value.int(0):
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond == "le":
                if v<=jvm.Value.int(0):
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond == "gt":
                if v > jvm.Value.int(0):
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond == "ge":
                if v >= jvm.Value.int(0):
                    frame.pc.offset = opr.target
                else:
                    frame.pc +=1
            return state
        

        
        case jvm.New(offset, classname):
            
            assert classname == jvm.ClassName("java/lang/AssertionError")

            return "assertion error"
        


        case jvm.If():
            v2 = frame.stack.pop()
            v1 = frame.stack.pop()
            cond = opr.condition

            assert isinstance(v1,jvm.Value), f"Expected JVM value, got a {v1!r}"
            assert isinstance(v2,jvm.Value), f"Expected JVM value, got a {v2!r}"
            assert cond in {"eq", "ne", "lt", "le", "gt", "ge"}, f"Unexpected condition {cond!r}"

            if cond == "ne":
                if v1!=v2:
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond =="eq":
                if v1==v2:
                    frame.pc.offset = opr.target
                else:
                    frame.pc +=1
            if cond == "lt":
                if v1<v2:
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond == "le":
                if v1<=v2:
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond == "gt":
                if v1 > v2:
                    frame.pc.offset = opr.target
                else:
                    frame.pc += 1
            if cond == "ge":
                if v1 >= v2:
                    frame.pc.offset = opr.target
                else:
                    frame.pc +=1
            return state

    
        
        case a:
            raise NotImplementedError(f"Don't know how to handle: {a!r}")







# #RUN RANDOM ANALYSIS -----------------------------------------------------------------

# def run_random_analysis(methodid, interpreter, num_trials=100):
#     """
#     Run dynamic analysis with random inputs.
    
#     - methodid: the function/method to analyze
#     - interpreter: your interpreter function that executes a method
#     - num_trials: how many random inputs to try
#     """
#     found_query_behavior = False  # Track if we ever see the query behavior

#     for _ in range(num_trials):
#         # 1. Generate random inputs based on method parameters
#         inputs = []
#         for param_type in methodid.extension.params:
#             if param_type == "int":
#                 # example: random integers from -10 to 10
#                 inputs.append(random.randint(-10, 10))
#             elif param_type == "bool":
#                 inputs.append(random.choice([True, False]))
#             # You can add more types if needed

#         # 2. Run the interpreter with these inputs
#         result = interpreter(methodid, inputs)

#         # 3. Check for query behavior
#         # Replace this with the actual condition you consider a "query behavior"
#         if result == "query_detected":  # <-- example
#             found_query_behavior = True
#             break  # stop early if you already found it

#     # 4. Emit percentages
#     if found_query_behavior:
#         print(f"{methodid.extension.name}: 100%")  # behavior observed
#     else:
#         print(f"{methodid.extension.name}: 50%")   # behavior not observed


# #END ------------------------------------------------------------------------------------





frame = Frame.from_method(methodid)






#DYNAMIC ANALYSIS:  ------------------------------------------------

# Loop over each input value provided for the method
for i, v in enumerate(input.values):
    # Convert JVM types to integer representations
    match v.type:
        case jvm.Boolean():  # If the value is a boolean
            # Convert True → 1, False → 0
            v = jvm.Value.int(1 if v.value else 0)
        case jvm.Int():  # If the value is already an integer
            # Just wrap it in a JVM Value object
            v = jvm.Value.int(v.value)
    
    # Store the converted value in the local variables of the frame
    frame.locals[i] = v


# Check if the method has parameters
if methodid.extension.params:  # has arguments
    # If the method takes arguments, we skip running it dynamically
    # Print 0% coverage for this case
    print(f"{methodid.extension.name}: 0%")
    
else:
    # If there are no arguments, it's safe to execute dynamically
    # Print 100% coverage for this case
    print(f"{methodid.extension.name}: 100%")


#END ---------------------------------------------------------------



state = State({}, Stack.empty().push(frame))


for x in range(1000):
    state = step(state)
    if isinstance(state, str):
        print(state)
        break
else:
    print("*")









