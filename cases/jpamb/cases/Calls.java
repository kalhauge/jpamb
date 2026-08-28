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
}
