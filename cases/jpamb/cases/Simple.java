package jpamb.cases;

import jpamb.utils.Case;

public class Simple {

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

  @Case("(false) -> assertion error")
  @Case("(true) -> ok")
  public static void assertBoolean(boolean shouldFail) {
    assert shouldFail;
  }

  @Case("(0) -> assertion error")
  @Case("(1) -> ok")
  public static void assertInteger(int n) {
    assert n != 0;
  }

  @Case("(-1) -> assertion error")
  @Case("(1) -> ok")
  public static void assertPositive(int num) {
    assert num > 0;
  }

  @Case("() -> divide by zero")
  public static int divideByZero() {
    return 1 / 0;
  }

  @Case("(0) -> divide by zero")
  @Case("(1) -> ok")
  public static int divideByN(int n) {
    return 1 / n;
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(0, 1) -> ok")
  public static int divideZeroByZero(int a, int b) {
    return a / b;
  }

  @Case("(false) -> assertion error")
  @Case("(true) -> divide by zero")
  public static int multiError(boolean b) {
    assert b;
    return 1 / 0;
  }

  @Case("() -> ok")
  public static int earlyReturn() {
    if (true) {
      return 0;
    }
    assert false;
    return 0;
  }

  @Case("(1) -> ok")
  @Case("(0) -> assertion error")
  public static int checkBeforeDivideByN(int n) {
    assert n != 0;
    return 1 / n;
  }

  @Case("(0) -> ok")
  public static int checkBeforeDivideByN2(int n) {
    if (n != 0) {
      return 1 / n;
    }
    assert 10 > n;
    return 0;
  }

  @Case("(-1) -> assertion error")
  @Case("(0) -> ok")
  public static void checkBeforeAssert(int n) {
    if (n == 0) {
      return;
    }
    assert 1 / n > 0;
  }

  @Case("() -> ok")
  public static int justReturn() {
    return 0;
  }

  @Case("(1, 2) -> ok")
  public static int justAdd(int a, int b) {
    return a + b;
  }

  @Case("(1, 2) -> ok")
  public static int justMulitply(int a, int b) {
    return a * b;
  }

  @Case("() -> ok")
  public static void justReturnNothing() {
    return;
  }

  @Case("(0) -> ok")
  @Case("(10054203) -> divide by zero")
  public static int divideByNMinus10054203(int n) {
    return 1 / (n - 10054203);
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(12, 3) -> ok")
  public static int directDivision(int numerator, int denominator) {
    return numerator / denominator;
  }

  @Case("(0) -> ok")
  @Case("(1) -> ok")
  public static int guardedDivision(int divisor) {
    if (divisor == 0) return 0;
    return 40 / divisor;
  }

  @Case("(false, 0) -> ok")
  @Case("(true, 0) -> divide by zero")
  public static int branchDivision(boolean shouldDivide, int divisor) {
    if (shouldDivide) return 10 / divisor;
    return 0;
  }

  @Case("(1, 0) -> divide by zero")
  @Case("(1, 2) -> ok")
  public static int nestedBranchDivision(int selector, int divisor) {
    if (selector > 0) {
      if (divisor == 0) return selector / divisor;
      return 10 / divisor;
    }
    if (divisor == 0) return selector / divisor;
    return 20 / divisor;
  }

  @Case("(true, 7, 0) -> ok")
  @Case("(false, 2, 0) -> divide by zero")
  public static int selectedDivisor(boolean useFirst, int first, int second) {
    int divisor = useFirst ? first : second;
    return 30 / divisor;
  }

  @Case("(5, 5) -> divide by zero")
  @Case("(5, 4) -> ok")
  public static int subtractForDivisor(int a, int b) {
    return 20 / (a - b);
  }

  // Testing Constant Extraction for strings lietrals and integers
  @Case("(0, s'other') -> ok")
  @Case("(1339, s'other') -> assertion error")
  @Case("(0, s'fuzz') -> assertion error")
  public static void ConstantExtractionCheck(int value, String name) {
    if (value == 1339) {
      assert false;
    }

    if ("fuzz".equals(name)) {
      assert false;
    }
  }

  // Boundary values - only one exact value triggers the assertion
  @Case("(4096) -> ok")
  @Case("(4097) -> assertion error")
  public static void integerRangeBoundary(int value) {
    if (value > 4096) {
      if (value < 4098) {
        assert false;
      }
    }
  }

  // Coverage - satisfied condition opens another branch (Retain partial progress)
  @Case("(31337, -27183, 0) -> ok")
  @Case("(31337, -27183, 65521) -> assertion error")
  public static void nestedConstantCoverage(int first, int second, int third) {
    if (first == 31337) {
      if (second == -27183) {
        if (third == 65521) {
          assert false;
        }
      }
    }
  }
}
