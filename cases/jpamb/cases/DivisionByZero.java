package jpamb.cases;

import jpamb.utils.Case;


public class DivisionByZero {

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

  @Case("(3, 0) -> divide by zero")
  @Case("(-2, 3) -> ok")
  public static int multiplyForDivisor(int a, int b) {
    return 20 / (a * b);
  }

  @Case("(0) -> divide by zero")
  @Case("(1) -> ok")
  public static int negatedDivisor(int divisor) {
    return 100 / -divisor;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 1) -> divide by zero")
  public static int forLoopDivision(int divisor, int iterations) {
    int result = 100;
    for (int i = 0; i < iterations; i++) result /= divisor;
    return result;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 2) -> divide by zero")
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
  public static int divisionChain(int value, int first, int second, int third) {
    return value / first / second / third;
  }

  private static int divideHelper(int numerator, int denominator) {
    return numerator / denominator;
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(10, 2) -> ok")
  public static int divisionThroughHelper(int numerator, int denominator) {
    return divideHelper(numerator, denominator);
  }

  @Case("(2, 0) -> divide by zero")
  @Case("(8, 3) -> ok")
  public static int directRemainder(int value, int divisor) {
    return value % divisor;
  }

  @Case("(false, 0) -> ok")
  @Case("(true, 0) -> divide by zero")
  public static int branchRemainder(boolean shouldRemainder, int divisor) {
    if (shouldRemainder) return 17 % divisor;
    return 0;
  }


  @Case("(0, 0) -> ok")
  @Case("(0, 1) -> divide by zero")
  public static int loopRemainder(int divisor, int iterations) {
    int result = 100;
    for (int i = 0; i < iterations; i++) result %= divisor;
    return result;
  }

// new cases for review :


  @Case("(9, 0) -> divide by zero")
  @Case("(9, 2) -> ok")
  // data type is long
  public static int longDivision(int value, int divisor) {
    return (int) ((long) value / (long) divisor);
  }

  @Case("(9, 0) -> divide by zero")
  @Case("(9, 2) -> ok")
  // test case to know if the analyzer correctly handles modulo operations long operands.
  public static int longRemainder(int value, int divisor) {
    return (int) ((long) value % (long) divisor);
  }

// data type long
/// Test case to know whether the analyzer 
// can identify a zero divisor resulting 
// from  exp (a - b).

  @Case("(5, 5) -> divide by zero")
  @Case("(5, 4) -> ok")
  public static int computeLongDivision(int a, int b) {
    return (int) (100L / ((long) a - (long) b));
  }

// data type long
// Tests whether the analyzer can detect zero divisors in computed expressions 
// involving long and modulo operations.
  @Case("(5, 5) -> divide by zero")
  @Case("(5, 4) -> ok")
  public static int computeLongRemainder(int a, int b) {
    return (int) (100L % ((long) a - (long) b));
  }


// below inlcude a bit complex cases for the analyzer
  @Case("(0, 5, 0) -> ok")
  @Case("(1, 21, 3) -> ok")
  // Tests whether the analyzer handles division and modulo safely
// inside nested if-else branches with zero checks.
  public static int safeNestedBranchDivision(int mode, int value, int divisor) {
    if (mode > 0) {
      if (divisor == 0) return value;
      return value / divisor;
    }
    if (mode < 0) {
      if (divisor == 0) return -value;
      return value % divisor;
    }
    return 0;
  }

  @Case("(0, 3, 10) -> ok")
  @Case("(2, 4, 0) -> ok")
  // Simulates repeated balance adjustments (adding and subtracting)
// inside a loop, after checking that the divisor is not zero.... exxmaple let say bank account (simulates a running balance with alternating deposits and deductions, where each adjustment is calculated using division.)
  public static int safeLoopAccumulation(int divisor, int count, int seed) {
    if (divisor == 0) return seed;
    int result = seed;
    for (int i = 1; i <= count && i <= 4; i++) {
      if (i % 2 == 0) result += i / divisor;
      else result -= (i + 1) / divisor;
    }
    return result;
  }

  @Case("(50, 5, 5) -> ok")
  @Case("(100, 9, 4) -> ok")
  // To test whether the analyzer can track safety checks
  //  across multiple dependent calculations and recogni the divisions etc if they are safe or not
  public static int safeDifferenceChain(int numerator, int left, int right) {
    int divisor = left - right;
    if (divisor == 0) return 0;
    int quotient = numerator / divisor;
    if (quotient == 0) return 0;
    return numerator / quotient;
  }


// similar kind of test cases for operations below as above
  @Case("(true, 0, 5, 20) -> ok")
  @Case("(false, -4, 2, 12) -> ok")
  public static int safeSelectedDivisor(
      boolean chooseFirst, int first, int second, int numerator) {
    int divisor;
    if (chooseFirst) divisor = first;
    else divisor = second;
    if (divisor == 0 || numerator == 0) return 0;
    int quotient = numerator / divisor;
    return quotient % divisor;
  }

  @Case("(0, 3, 3) -> ok")
  @Case("(2, 3, 3) -> ok")
  public static int safeNestedLoopDivision(
      int divisor, int outerCount, int innerCount) {
    if (divisor == 0) return 0;
    int result = 0;
    for (int outer = 0; outer < outerCount && outer < 3; outer++) {
      for (int inner = 0; inner < innerCount && inner < 3; inner++) {
        result += (outer + inner + 1) / divisor;
      }
    }
    return result;
  }

  @Case("(1, 4, 4, 1, 20) -> divide by zero")
  @Case("(1, 5, 3, 1, 20) -> ok")
  public static int unsafeNestedAffineDivisor(
      int selector, int a, int b, int offset, int numerator) {
    int difference = a - b;
    if (selector > 0) return numerator / difference;
    if (selector == 0) return numerator % (difference + offset);
    return numerator / (difference - offset);
  }

  @Case("(-1, 0, 4, 10) -> divide by zero")
  @Case("(1, 5, 2, 9) -> ok")
  public static int unsafeModeDerivedDivisor(
      int mode, int left, int right, int numerator) {
    int divisor;
    if (mode < 0) divisor = left * right;
    else if (mode == 0) divisor = left + right;
    else divisor = left - right;
    return numerator / divisor;
  }

  @Case("(0, 5, 0, 10) -> divide by zero")
  @Case("(4, 1, 2, 20) -> ok")
  public static int unsafeLoopOffsetDivisor(
      int start, int step, int count, int numerator) {
    int divisor = start;
    for (int i = 0; i < count && i < 5; i++) {
      divisor += step;
      if (i % 2 == 0) divisor--;
    }
    return numerator / divisor;
  }

  @Case("(0, 4, 0, 0, 10) -> divide by zero")
  @Case("(10, 2, 2, 2, 20) -> ok")
  public static int unsafeNestedLoopDivisor(
      int base, int step, int outerCount, int innerCount, int numerator) {
    int divisor = base;
    for (int outer = 0; outer < outerCount && outer < 3; outer++) {
      for (int inner = 0; inner < innerCount && inner < 3; inner++) {
        divisor += step - outer - inner;
      }
    }
    return numerator / divisor;
  }

  @Case("(1, 3, 4, -12, 20) -> divide by zero")
  @Case("(0, 3, 4, -11, 20) -> ok")
  public static int unsafeComputedRemainder(
      int selector, int left, int right, int offset, int numerator) {
    int divisor = left * right + offset;
    if (selector > 0) return numerator % divisor;
    return (numerator + 1) / (divisor + selector);
  }
}
