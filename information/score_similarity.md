# Why are some analysis scores so similar?

Our abstractions remember different information. But the benchmark scores the
**final predicted outcomes**, not how much information an abstraction remembers.
A more precise value only helps the score if it changes a prediction.

For example, knowing that a result is exactly 8 instead of merely positive may
make no difference when the method simply returns normally.

## What the current results show

These are the recorded full-suite scores after adding array support. Each run
used the same 47 benchmark methods and three iterations.

| Configuration | Score |
| --- | ---: |
| Sign | 146.20 |
| Interval | 156.15 |
| Sign + interval | 156.15 |
| Sign + string | 148.74 |
| Interval + string | 158.62 |
| Sign + interval + string | 158.62 |
| String only | 72.90 |

Comparing the saved reports confirms:

- Interval and sign + interval make identical predictions on all 47 methods.
- Interval + string and all three domains make identical predictions too.
- Interval changes predictions compared with sign in five array methods.
- Adding strings to interval changes predictions for just `Strings.sayHello`.

So these equal scores really do come from equal predictions in this run. In
general, equal totals alone are not enough evidence: improvements and losses
could cancel out. JPAMB also calibrates its prediction categories across the run,
so per-method predictions are more useful than simply subtracting total scores.

## The suite does show some differences

Intervals already help with these methods:

| Method | Improvement compared with sign analysis |
| --- | --- |
| `Arrays.arrayInBounds` | Excludes an unnecessary bounds error |
| `Arrays.arrayLength` | Excludes unnecessary bounds and assertion errors |
| `Arrays.arrayContentAboveMinus13` | Excludes an unnecessary assertion error |
| `Arrays.arrayOutOfBounds` | Excludes normal completion |
| `Arrays.arraySometimesNull` | Excludes normal completion |

For example, signs describe both index 1 and length 2 as positive. That is not
enough to decide whether the index is smaller than the length. Intervals can
retain `[1,1]` and `[2,2]`, and establish that the access is within bounds.

The suite is therefore useful. It just does not currently produce different
final answers for every pair of our configurations.

## Why adding signs to intervals often changes nothing

An interval can already imply a sign:

```text
Interval [2, 8] means the value is positive.
Adding the sign {positive} tells us nothing new.
```

But an interval cannot express every useful fact:

```text
The value is either -5 or 5.

Interval:        [-5, 5] — includes zero.
Signs:           {negative, positive} — excludes zero.
Combined domain: [-5, 5], with zero excluded.
```

Here the domains complement each other. To see a scoring difference, a program
must actually use that extra information in a way that changes an outcome.

## The interpreter also limits the benefit

### Conditions do not yet narrow stored values

```java
if (n != 0) {
    return 10 / n;
}
return 0;
```

Inside the true branch, a person knows that `n` is not zero. Our interpreter
currently follows the branch without updating the stored description of `n`.
It may therefore still predict division by zero.

Signs and the combined domain could represent the nonzero fact, but the
interpreter has not passed that fact to them. Branch refinement is a separate
improvement. A single interval still cannot represent a hole at zero, even after
refinement; it can represent a condition such as `n > 0` as `[1, MAX]` instead.

### Arrays summarize all positions together

For `[2, 5, 8]`, interval mode stores an element summary `[2, 8]`.
Reading position 0 returns that summary rather than exactly 2. Weak writes also
retain previous possible values, including initial zeros. This is conservative,
but it can hide differences that more detailed element tracking would expose.

### Some instructions are still unsupported

Array support removed a major coverage gap, but general method calls and some
casts are still unsupported. A more precise numeric domain does not supply those
missing instruction handlers.

### There is only one Java String benchmark method

`Strings.sayHello` is the only existing benchmark method using Java String.
`Arrays.arraySpellsHello` uses `char[]`, which is handled by array support.
String-only mode is not expected to perform well on this mostly numeric suite.

## Example methods we could add

The examples below are proposals, not methods already added to the suite. They
are deliberately small so each tests one difference. Expected differences concern
the listed errors; our analyzer still reports nontermination as unknown.

### 1. Show why numeric bounds help

```java
static void boundedAddition(boolean choice) {
    int x;
    if (choice) {
        x = 2;
    } else {
        x = 5;
    }
    assert x + 3 < 10;
}
```

Interval analysis combines the branches into `[2,5]`. Adding 3 gives `[5,8]`, so
it can exclude assertion failure. Sign analysis has less information and its
conservative Java arithmetic rules allow an assertion failure.

This distinguishes sign analysis from interval and combined analysis.

### 2. Show information that intervals lose

```java
static int nonzeroDivisor(boolean choice) {
    int divisor;
    if (choice) {
        divisor = -5;
    } else {
        divisor = 5;
    }
    return 10 / divisor;
}
```

Interval analysis joins the divisor values into `[-5,5]`, which includes zero,
and may report division by zero. Signs retain `{negative,positive}` and exclude
that error. The combined domain also excludes it.

Unlike the earlier guarded-input example, this obtains the nonzero information
from assignments. It does not require branch refinement to demonstrate the benefit.

### 3. Show why the combined domain can help with two questions

```java
static void nonzeroAndBounded(boolean choice) {
    int divisor;
    if (choice) {
        divisor = -5;
    } else {
        divisor = 5;
    }
    int result = 10 / divisor;
    assert result >= -10 && result <= 10;
}
```

The real result is either -2 or 2. We use wider assertion bounds because the
abstract divisor also includes other nonzero values between -5 and 5.

| Mode | What it can establish |
| --- | --- |
| Sign | Divisor is nonzero, but result bounds are too imprecise |
| Interval | Normal result is within [-10,10], but zero divisor is still possible |
| Sign + interval | Divisor is nonzero and normal result is within [-10,10] |

This is a useful candidate for distinguishing the combined domain from each
individual integer domain. Existing synthetic interpreter tests already check
the nonzero-division behavior; Java benchmark methods would make it part of scoring.

### 4. Show string and numeric analysis cooperating

```java
static void greetingAndBound(boolean choice) {
    String greeting;
    int x;
    if (choice) {
        greeting = "hello";
        x = 2;
    } else {
        greeting = "bye";
        x = 5;
    }
    assert greeting.equals("hello");
    assert x + 3 < 10;
}
```

The false branch can fail the greeting assertion. Interval + string can also
establish that the numeric assertion is safe, including after the states join.
String-only mode cannot perform the integer arithmetic; numeric-only modes cannot
execute the string operations.

However, both assertions use the same final category, `assertion error`. A false
warning at the second assertion may be hidden by the real failure at the first.
To measure the numeric improvement clearly, use a variant that assigns `"hello"`
on both branches, or split the assertions into separate benchmark methods. This
is an example of why richer code does not automatically make a better test.

### 5. Test branch refinement separately when it is added

```java
static int positiveDivisor(int n) {
    if (n > 0) {
        return 10 / n;
    }
    return 0;
}
```

No execution divides by zero. After branch refinement is implemented, all integer
domains should be able to exclude that error. Until then, this tests an interpreter
limitation rather than a missing interval arithmetic rule.

## How to build useful accuracy tests

- Keep each method small and target one behavior.
- Include both safe methods and methods that really can fail.
- Compare predicted outcomes method by method, not only the total score.
- Check that every real outcome is included, then count unnecessary warnings.
- Use constant/branch examples first; they are easier to reason about than loops.
- Add loop and aliasing cases separately to test widening and heap behavior.
- Do not silently treat an unsupported operation as a safe program.

When adding real benchmark entries, follow the existing
[benchmark extension guide](../docs/extending-jpamb.md) and add appropriate
`@Case` inputs and outcomes. Current scores are a baseline, not a target to achieve
by tailoring the analyzer to benchmark annotations.

For execution commands see the [static analyzer README](../solutions/static/README.md).
For representation details see [the implementation notes](static_analysis.md).
