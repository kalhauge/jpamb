package jpamb.cases;

import jpamb.utils.Case;

public class MagicConstants {

  @Case("(42) -> assertion error")
  @Case("(1) -> ok")
  public static void sumReachesTarget(int x) {
    int sum = 0;
    for (int i = 0; i < x; i++) {
      sum += 2;
    }
    assert sum != 84;
  }

  @Case("(5) -> out of bounds")
  @Case("(0) -> ok")
  public static int computedIndex(int x) {
    int[] arr = new int[3];
    int idx = x * 2 - 7;
    if (idx >= 0) {
      return arr[idx];
    }
    return 0;
  }

  @Case("(50) -> null pointer")
  @Case("(0) -> ok")
  public static int derivedNull(int x) {
    int[] arr = new int[1];
    if (x + x == 100) {
      arr = null;
    }
    return arr[0];
  }

  @Case("(10) -> divide by zero")
  @Case("(3) -> ok")
  public static int squaredDivisor(int x) {
    return 1 / (x * x - 100);
  }

  @Case("(25) -> assertion error")
  @Case("(4) -> ok")
  public static void squareThreshold(int x) {
    assert x * x != 625;
  }
}