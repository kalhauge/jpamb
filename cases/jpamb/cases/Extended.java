/* Cases that uses combination of operators, loops or other.
 * These are generally harder than the Simple cases.
 */

package jpamb.cases;

import jpamb.utils.Case;

public class Extended {

  @Case("(0, 3, 10) -> ok")
  @Case("(2, 4, 0) -> ok")
  // Simulates repeated balance adjustments (adding and subtracting)
  // inside a loop, after checking that the divisor is not zero.... exxmaple let say bank account
  // (simulates a running balance with alternating deposits and deductions, where each adjustment is
  // calculated using division.)
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
  public static int safeSelectedDivisor(boolean chooseFirst, int first, int second, int numerator) {
    int divisor;
    if (chooseFirst) divisor = first;
    else divisor = second;
    if (divisor == 0 || numerator == 0) return 0;
    int quotient = numerator / divisor;
    return quotient % divisor;
  }

  @Case("(0, 3, 3) -> ok")
  @Case("(2, 3, 3) -> ok")
  public static int safeNestedLoopDivision(int divisor, int outerCount, int innerCount) {
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
  public static int unsafeModeDerivedDivisor(int mode, int left, int right, int numerator) {
    int divisor;
    if (mode < 0) divisor = left * right;
    else if (mode == 0) divisor = left + right;
    else divisor = left - right;
    return numerator / divisor;
  }

  @Case("(0, 5, 0, 10) -> divide by zero")
  @Case("(4, 1, 2, 20) -> ok")
  public static int unsafeLoopOffsetDivisor(int start, int step, int count, int numerator) {
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
