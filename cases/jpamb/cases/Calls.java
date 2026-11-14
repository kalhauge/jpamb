package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Tag;

public class Calls {

  public static void assertTrue() {
    assert true;
  }

  public static void assertFalse() {
    assert false;
  }

  public static void assertIf(boolean test) {
    if (test) {
      assertTrue();
    } else {
      assertFalse();
    }
  }

  @Case("() -> ok")
  public static void callsAssertTrue() {
    assertTrue();
  }

  @Case("() -> assertion error")
  @Tag({CALL})
  public static void callsAssertFalse() {
    assertFalse();
  }

  @Case("(true) -> ok")
  @Case("(false) -> assertion error")
  @Tag({CALL})
  public static void callsAssertIf(boolean b) {
    assertIf(b);
  }

  @Case("() -> ok")
  @Tag({CALL})
  public static void callsAssertIfWithTrue() {
    assertIf(true);
  }

  public static int fib(int i) {
    assert i >= 0;
    if (i == 0 || i == 1) return i;
    return fib(i - 1) + fib(i - 2);
  }

  @Case("(8) -> ok")
  @Case("(0) -> assertion error")
  @Tag({CALL, RECURSION})
  public static void callsAssertFib(int i) {
    assert fib(i) == 21;
  }

  public static int[] generatePrimeArray(int length) {
    assert length >= 0;
    int[] primeArray = new int[length];
    primeArray[0] = 2;
    int count = 1, number = 3;

    while (count < length) {
      boolean isprime = true;
      for (int p : primeArray) {
        isprime = number % p != 0;
        if (!isprime || p * p > number) {
          break;
        }
      }
      if (isprime) {
        primeArray[count] = number;
        count++;
      }
      number++;
    }

    return primeArray;
  }

  @Case("(100) -> ok")
  @Case("(0) -> out of bounds")
  @Case("(-1) -> assertion error")
  @Tag({CALL, ARRAY, LOOP, INTEGER_OVERFLOW})
  public static void allPrimesArePositive(int number) {
    for (int p : generatePrimeArray(number)) {
      assert p > 0;
    }
  }

  public static int boundSize(int requested) {
    if (requested <= 0) {
      return 10;
    }
    if (requested > 50) {
      return 50;
    }
    return requested;
  }

  @Case("(1, 20) -> ok")
  @Case("(-1, 20) -> assertion error")
  @Tag({CALL})
  public static int callsCallChain(int depth, int requested) {
    assert depth >= 0;
    return callsCallCycle(depth, requested);
  }

  @Case("(1, 20) -> ok")
  @Tag({CALL, RECURSION})
  public static int callsCallCycle(int depth, int requested) {
    if (depth <= 0) {
      return requested;
    }
    return callsCallCycleNext(depth, requested);
  }

  @Case("(1, 20) -> ok")
  @Tag({CALL, RECURSION})
  public static int callsCallCycleNext(int depth, int requested) {
    return callsCallCycleFork(depth, requested);
  }

  @Case("(1, 20) -> ok")
  @Tag({CALL, RECURSION})
  public static int callsCallCycleFork(int depth, int requested) {
    int size = boundSize(requested);
    return callsCallCycleLoop(depth - 1, size);
  }

  @Case("(0, 20) -> ok")
  @Tag({CALL, RECURSION})
  public static int callsCallCycleLoop(int depth, int size) {
    return callsCallCycle(depth, size);
  }

  public static int diamondSink(int x) {
    assert x >= 0;
    return x;
  }

  public static int diamondLeft(int x) {
    return diamondSink(x);
  }

  public static int diamondRight(int x) {
    return diamondSink(x);
  }

  @Case("(1) -> ok")
  @Case("(-1) -> assertion error")
  @Tag({CALL})
  public static int callsDiamond(int x) {
    return diamondLeft(x) + diamondRight(x);
  }

  public static int bowtieLeft(int n, int x) {
    return bowtieLeftBack(n, x);
  }

  public static int bowtieLeftBack(int n, int x) {
    return callsBowtie(n - 1, x);
  }

  public static int bowtieRight(int n, int x) {
    return bowtieRightBack(n, x);
  }

  public static int bowtieRightBack(int n, int x) {
    return callsBowtie(n - 1, x);
  }

  @Case("(1, 3) -> ok")
  @Case("(-1, 3) -> assertion error")
  @Tag({CALL, RECURSION})
  public static int callsBowtie(int n, int x) {
    assert n >= 0;
    if (n == 0) {
      return x;
    }
    return bowtieLeft(n, x) + bowtieRight(n, x);
  }

  public static int tadpoleCycle(int n, int x) {
    if (n <= 0) {
      return x;
    }
    return tadpoleCycleNext(n - 1, x + 1);
  }

  public static int tadpoleCycleNext(int n, int x) {
    return tadpoleCycle(n, x);
  }

  public static int tadpoleTail(int n, int x) {
    return tadpoleCycle(n, x);
  }

  @Case("(1, 2) -> ok")
  @Case("(-1, 2) -> assertion error")
  @Tag({CALL, RECURSION})
  public static int callsTadpole(int n, int x) {
    assert n >= 0;
    return tadpoleTail(n, x);
  }

  public static int dumbbellLeft(int n, int x) {
    if (n <= 0) {
      return x;
    }
    return dumbbellLeftNext(n - 1, x + 1);
  }

  public static int dumbbellLeftNext(int n, int x) {
    return dumbbellLeft(n, x);
  }

  public static int dumbbellRight(int n, int x) {
    if (n <= 0) {
      return x;
    }
    return dumbbellRightNext(n - 1, x + 1);
  }

  public static int dumbbellRightNext(int n, int x) {
    return dumbbellRight(n, x);
  }

  public static int dumbbellBridge(int n, int x) {
    return dumbbellRight(n, dumbbellLeft(n, x));
  }

  @Case("(1, 2) -> ok")
  @Case("(-1, 2) -> assertion error")
  @Tag({CALL, RECURSION})
  public static int callsDumbbell(int n, int x) {
    assert n >= 0;
    return dumbbellBridge(n, x);
  }

  public static int wheelRimA(int n, int x) {
    if (n <= 0) {
      return x;
    }
    return wheelRimB(n - 1, x + 1);
  }

  public static int wheelRimB(int n, int x) {
    return wheelRimC(n, x);
  }

  public static int wheelRimC(int n, int x) {
    return wheelRimA(n, x);
  }

  public static int wheelSpokeA(int n, int x) {
    return wheelRimA(n, x);
  }

  public static int wheelSpokeB(int n, int x) {
    return wheelRimB(n, x);
  }

  public static int wheelSpokeC(int n, int x) {
    return wheelRimC(n, x);
  }

  @Case("(1, 2) -> ok")
  @Case("(-1, 2) -> assertion error")
  @Tag({CALL, RECURSION})
  public static int callsWheel(int n, int x) {
    assert n >= 0;
    return wheelSpokeA(n, x) + wheelSpokeB(n, x) + wheelSpokeC(n, x);
  }

  private static int divideHelper(int numerator, int denominator) {
    return numerator / denominator;
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(10, 2) -> ok")
  public static int divisionThroughHelper(int numerator, int denominator) {
    return divideHelper(numerator, denominator);
  }

  // The division only exists in the callee, so an analysis must
  // follow calls.
  public static int scale(int x, int d) {
    return x / d;
  }

  @Case("(3) -> divide by zero")
  @Case("(0) -> ok")
  @Tag({CALL})
  public static int divideViaHelper(int n) {
    return scale(100, n - 3);
  }
}
