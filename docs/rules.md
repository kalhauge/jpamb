# Rules

The goal of this benchmark suite is to build a program that analyzes Java methods and predicts what will can happen when they run with any input.

## What is a Case?

A Java method is annotated with cases.
A case is an input that causes some behavior.
Consider the following example:

```java
@Case("(1) -> ok")
@Case("(0) -> assertion error")
public static int checkBeforeDivideByN(int n) {
    assert n != 0;
    return 1 / n;
}
```

This method is annotated with `(1) -> ok` and `(0) -> assertion error`, meaning that if `n = 1`, we expect the program to complete successfully, whereas if we run the program with `n = 0`, we expect it to trigger an assertion error.

The cases of a method is exhaustive, which mean that if a behavior is not listed, it
is not possible.

Your analyzer need to predict if there exist an input to the method where one
of these possible behaviors can happen:

| Outcome           | What it means                                   |
| :---------------- | :---------------------------------------------- |
| `ok`              | Method runs and finishes normally               |
| `divide by zero`  | Method tries to divide by zero                  |
| `assertion error` | Method fails an assertion (like `assert x > 0`) |
| `out of bounds`   | Method accesses array outside its bounds        |
| `null pointer`    | Method tries to use a null reference            |
| `*`               | Method runs forever (infinite loop)             |

## Making Predictions

For each outcome, you give either:

- **A wager**: `5` means "bet 5 points this will happen", `-10` means "bet 10 points this WON'T happen"
- **A percentage**: `75%` means "75% of all methods that looks like this will have this outcome"
- **A category** (preferred): `yes` means "group all my yes predictions, and give a wager which maximizes my score across the benchmark suite". For example you can give all outcomes you deem likely a `yes` and all unlikely a `no`. If you have done so correctly all `yes` outcomes will get a large positive wager, and all unlikely get a large negative wager.

For example, consider these two methods. We need to predict ( without cheating and looking at the cases), if each of them fails an assertion.

```java
@Case("() -> assertion error")
public static void assertFalse() {
    assert false;
}

@Case("() -> ok")
public static void assertTrue() {
    assert true;
}

@Case("() -> ok")
public static void doNothing() {}
```

One trivial approach is to check if there is an `assert` in the method.
If we are certain of this, we can wager `inf` points if `assert` is in the method and `-inf` if not.
This works for `assertFalse` and `doNothing` but not for `assertTrue`; so even though we gain one point for `assertFalse` and `doNothing`, we lose infinite points for `assertTrue`.
We can, of course, hedge our bets and only bet 1 point, which gives us 1/2 a point for `assertFalse` and `doNothing`, but we lose only 1 point for `assertTrue`, resulting in a total of 0 points.

To ease this calibration, we can provide a **percentage**.
If a method contains `assert`, we can say that we are `50%` sure that the method will throw an assertion error for some input, but if not, we are sure that `0%` of assertions are thrown.
This is converted into an ideal wager (in this case, 0 and -inf points), which results in a total of 1 point.

Because calculating this probability over the benchmark suite is error-prone, we have a final option: emitting a **category**, such as `yes` or `no`.
We can choose any combination of letters (except for `inf` and `nan`), and it will group predictions and provide the ideal **percentage**, which is again translated into a **wager**.
In the above example, we could assign `yes` to all methods with an `assert` and `no` to every method without one.
The benchmark suite will then calculate the `50%` and `0%` values mentioned above.

### In detail: Wagers

Every prediction is turned into a **wager**, which essentially is betting points according to
how sure you are in your prediction:

- Positive wager (e.g., `divide by zero;5`) means "I bet 5 points this WILL happen"
- Negative wager (e.g., `divide by zero;-10`) means "I bet 10 points this WON'T happen"
- Higher wagers = higher risk/reward

The scoring formula: `points = 1 - 1/(|wager| + 1)` if you win, `-|wager|` if you lose.

When using percentages, an optimal **wager** is placed on your behalf, which takes into
account that you think that the probability that a method will emit this behaviour under
any input is $p$.

This is calculated like this:

```python
sign = 1
if p < 0.5: p = 1 - p; sign = -1
if p == 1:
    return sign * float("inf")
else:
    return sign * (1 - 2 * p) / (-1 + p) / 2
```

## Writing an Analysis

Here we use `./your_analyzer` to be name of the program you are going to write.
It has to support two modes:

**1. Info command** - tells us about your analyzer:

```bash
$ ./your_analyzer info
```

This should output 5 lines:

- Your analyzer's name
- Version number
- Your team/group name
- Tags describing your approach (e.g., "static,dataflow")
- Either your system info (to help us improve and for science) or "no" (for privacy)

```
bytecoder
1.0
The Rice Theorem Cookers
syntatic,python
Linux-6.18.43-x86_64-with-glibc2.42
```

**2. Analysis command** - makes predictions:

```bash
$ ./your_analyzer "jpamb.cases.Simple.divideByZero:()I"
```

One example output might look like this:

```
ok;90%
divide by zero;yes
assertion error;5%
out of bounds;0%
null pointer;no
*;maybe
```

**Assumptions**

You can rely on the following assumptions:

1. Your program will always run in the JPAMB folder. This means that you can access files like `cases/jpamb/cases/Simple.java` from your program.

2. All methods presented to the analysis comes from files in the `cases/jpamb/cases` folder, and can be uniquely identified by their method name.

3. Only the stdout is captured by JPAMB, so you can output debug information in the stderr.

## Evaluation

To evaluate your analysis you have to run the following command, from the JPAMB folder:

```bash
$ uv run jpamb analyse ./your_analyser
```

To get a shareable json report, you can run the following:

```bash
$ uv run jpamb analyse --format=json ./your_analyser > report.json
```
