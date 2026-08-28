package jpamb.cases;

import jpamb.utils.Case;

public class Dependent {

  @Case("(0) -> ok")
  @Case("(1) -> ok")
  public static int safeDivByN(int n) {
    if (n != 0) {
      return 1 / n;
    }
    return 0;
  }

  @Case("(0, 0) -> ok")
  public static int normalizedDistance(int x, int y) {
    int dst = y - x;
    if (dst == 0) {
      return 0;
    }
    if (x < 0) x = -x;
    if (y < 0) y = -y;
    if (x >= y) {
      return dst / x;
    } else {
      return dst / y;
    }
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(1, 1) -> ok")
  public static int badNormalizedDistance(int x, int y) {
    int dst = y - x;
    if (x < 0) x = -x;
    if (y < 0) y = -y;
    if (x >= y) {
      return dst / x;
    } else {
      return dst / y;
    }
  }

  @Case("(0) -> ok")
  @Case("(1) -> ok")
  public static void divisionLoop(int n) {
    for (int i = 0; i < 5; i++) { // 1024 / 2^5 = 32
      n /= 2;
    }
    assert n != 32;
  }
}
