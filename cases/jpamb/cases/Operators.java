/* Cases testing basic operators beyond the ones used in Simple
 */
package jpamb.cases;

import jpamb.utils.Case;

public class Operators {

  @Case("(20, 2, 1, 1) -> ok")
  @Case("(20, 0, 1, 1) -> divide by zero")
  public static int divisionChain(int value, int first, int second, int third) {
    return value / first / second / third;
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
}
