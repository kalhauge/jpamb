package jpamb.cases;

import jpamb.utils.Case;

public class DivisionByZero {

  @Case("(0, 0) -> divide by zero")
  @Case("(12, 3) -> ok")
  @Case("(-12, 3) -> ok")
  @Case("(12, -3) -> ok")
  @Case("(-12, -3) -> ok")
  public static int directDivision(int numerator, int denominator) {
    return numerator / denominator;
  }

  @Case("(0) -> ok")
  @Case("(1) -> ok")
  @Case("(-2) -> ok")
  @Case("(40) -> ok")
  @Case("(-40) -> ok")
  public static int guardedDivision(int divisor) {
    if (divisor == 0) return 0;
    return 40 / divisor;
  }

  @Case("(false, 0) -> ok")
  @Case("(true, 0) -> divide by zero")
  @Case("(true, 2) -> ok")
  @Case("(false, 5) -> ok")
  @Case("(true, -1) -> ok")
  public static int branchDivision(boolean shouldDivide, int divisor) {
    if (shouldDivide) return 10 / divisor;
    return 0;
  }

  @Case("(1, 0) -> divide by zero")
  @Case("(1, 2) -> ok")
  @Case("(-1, 0) -> divide by zero")
  @Case("(-1, 2) -> ok")
  @Case("(0, -2) -> ok")
  public static int nestedBranchDivision(int selector, int divisor) {
    if (selector > 0) {
      if (divisor == 0) return selector / divisor;
      return 10 / divisor;
    }
    if (divisor == 0) return selector / divisor;
    return 20 / divisor;
  }

  @Case("(true, 7, 0) -> ok")
  @Case("(true, 7, 2) -> ok")
  @Case("(false, 0, 0) -> divide by zero")
  @Case("(false, 2, 0) -> divide by zero")
  @Case("(false, 0, 3) -> ok")
  public static int selectedDivisor(boolean useFirst, int first, int second) {
    int divisor = useFirst ? first : second;
    return 30 / divisor;
  }

  @Case("(5, 5) -> divide by zero")
  @Case("(5, 4) -> ok")
  @Case("(4, 5) -> ok")
  @Case("(-2, -2) -> divide by zero")
  @Case("(0, 3) -> ok")
  public static int subtractForDivisor(int a, int b) {
    return 20 / (a - b);
  }

  @Case("(3, 0) -> divide by zero")
  @Case("(0, 3) -> divide by zero")
  @Case("(-2, 3) -> ok")
  @Case("(-2, -3) -> ok")
  @Case("(5, 2) -> ok")
  public static int multiplyForDivisor(int a, int b) {
    return 20 / (a * b);
  }

  @Case("(0) -> divide by zero")
  @Case("(1) -> ok")
  @Case("(-1) -> ok")
  @Case("(2) -> ok")
  @Case("(-3) -> ok")
  public static int negatedDivisor(int divisor) {
    return 100 / -divisor;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 1) -> divide by zero")
  @Case("(2, 3) -> ok")
  @Case("(-2, 2) -> ok")
  @Case("(3, -1) -> ok")
  public static int forLoopDivision(int divisor, int iterations) {
    int result = 100;
    for (int i = 0; i < iterations; i++) result /= divisor;
    return result;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 2) -> divide by zero")
  @Case("(2, 3) -> ok")
  @Case("(-1, 1) -> ok")
  @Case("(4, -1) -> ok")
  public static int whileLoopDivision(int divisor, int iterations) {
    int result = 100;
    int i = 0;
    while (i < iterations) {
      result /= divisor;
      i++;
    }
    return result;
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(2, 0) -> ok")
  @Case("(0, 3) -> divide by zero")
  @Case("(3, 2) -> ok")
  @Case("(-2, 1) -> ok")
  public static int doWhileDivision(int divisor, int iterations) {
    int result = 100;
    int i = 0;
    do {
      result /= divisor;
      i++;
    } while (i < iterations);
    return result;
  }

  @Case("(20, 2, 1, 1) -> ok")
  @Case("(20, 0, 1, 1) -> divide by zero")
  @Case("(20, 2, 0, 1) -> divide by zero")
  @Case("(0, 2, 1, 0) -> divide by zero")
  @Case("(0, 2, 1, 1) -> ok")
  public static int divisionChain(int value, int first, int second, int third) {
    return value / first / second / third;
  }

  private static int divideHelper(int numerator, int denominator) {
    return numerator / denominator;
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(10, 2) -> ok")
  @Case("(-10, 2) -> ok")
  @Case("(10, -2) -> ok")
  @Case("(0, 3) -> ok")
  public static int divisionThroughHelper(int numerator, int denominator) {
    return divideHelper(numerator, denominator);
  }

  @Case("(2, 0) -> divide by zero")
  @Case("(2, 1) -> ok")
  @Case("(-2, 1) -> ok")
  @Case("(8, 3) -> ok")
  @Case("(-8, -3) -> ok")
  public static int directRemainder(int value, int divisor) {
    return value % divisor;
  }

  @Case("(false, 0) -> ok")
  @Case("(true, 0) -> divide by zero")
  @Case("(true, 3) -> ok")
  @Case("(false, 2) -> ok")
  @Case("(true, -3) -> ok")
  public static int branchRemainder(boolean shouldRemainder, int divisor) {
    if (shouldRemainder) return 17 % divisor;
    return 0;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 1) -> divide by zero")
  @Case("(3, 2) -> ok")
  @Case("(-3, 2) -> ok")
  @Case("(5, -1) -> ok")
  public static int loopRemainder(int divisor, int iterations) {
    int result = 100;
    for (int i = 0; i < iterations; i++) result %= divisor;
    return result;
  }

  @Case("(9, 0) -> divide by zero")
  @Case("(9, 2) -> ok")
  @Case("(-9, 2) -> ok")
  @Case("(9, -2) -> ok")
  @Case("(0, -3) -> ok")
  public static int longDivision(int value, int divisor) {
    return (int) ((long) value / (long) divisor);
  }

  @Case("(9, 0) -> divide by zero")
  @Case("(9, 2) -> ok")
  @Case("(-9, 2) -> ok")
  @Case("(9, -2) -> ok")
  @Case("(0, -3) -> ok")
  public static int longRemainder(int value, int divisor) {
    return (int) ((long) value % (long) divisor);
  }

  @Case("(5, 5) -> divide by zero")
  @Case("(5, 4) -> ok")
  @Case("(4, 5) -> ok")
  @Case("(-2, -2) -> divide by zero")
  @Case("(0, 3) -> ok")
  public static int computedLongDivision(int a, int b) {
    return (int) (100L / ((long) a - (long) b));
  }

  @Case("(5, 5) -> divide by zero")
  @Case("(5, 4) -> ok")
  @Case("(4, 5) -> ok")
  @Case("(-2, -2) -> divide by zero")
  @Case("(0, 3) -> ok")
  public static int computedLongRemainder(int a, int b) {
    return (int) (100L % ((long) a - (long) b));
  }
}
