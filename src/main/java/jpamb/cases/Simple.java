package jpamb.cases;

import jpamb.utils.Case;

public class Simple {

  @Case("() -> assertion error")
  public static void assertFalse() {
    assert false;
  }

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
  @Case("(1) -> ok")
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

  @Case("(0) -> ok")
  @Case("(1087) -> divide by zero")
  public static int divideByZeroHidden(int n) {
    if (n == 1087) {
        return 1 / 0;
    }
    return n;
  }

  @Case("(3) -> ok")
  @Case("(17) -> assertion error")
  public static int assertFalseHidden(int n) {
    int x = n - 3;
    int y = 2 * x;
    if (y == 28) {
        assert false;
    }
    return n;
  }

  @Case("(2) -> ok")
  @Case("(1) -> assertion error")
  public static int assertFalseIfOdd(int n) {
    int x = n % 2;
    if (x == 1) {
        assert false;
    }
    return n;
  }

}
