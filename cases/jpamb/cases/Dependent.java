package jpamb.cases;

import jpamb.utils.Case;

public class Dependent {

  @Case("(0) -> ok")
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
  @Case("(1024) -> assertion error")
  public static void divisionLoop(int n) {
    for (int i = 0; i < 5; i++) { // 1024 / 2^5 = 32
      n /= 2;
    }
    assert n != 32;
  }

  // The compared target depends on another argument.
  // For base = 100, the runtime comparison exposes 3017.
  @Case("(100, 0) -> ok")
  @Case("(100, 3017) -> assertion error")
  public static void compareEquality(int base, int candidate) {
    if (base < 100) {
      return;
    }
    if (base > 1000) {
      return;
    }

    int target = base * 30 + 17;
    if (candidate == target) {
      assert false;
    }
  }

  @Case("(24691, 400, 12013) -> ok")
  @Case("(24691, 400, 12014) -> assertion error")
  public static void combinedGuidance(int gate, int base, int candidate) {
    if (gate != 24691) {
      return;
    }
    if (base < 400) {
      return;
    }
    if (base > 900) {
      return;
    }

    int target = base * 30 + 13;
    if (candidate > target) {
      if (candidate < target + 2) {
        assert false;
      }
    }
  }

  // The assertion is unreachable because n * 2 is always even.
  @Case("(7) -> ok")
  public static void doubleIsAlwaysEven(int n) {
    int x = n * 2;
    if (x % 2 != 0) {
      assert false;
    }
  }
}
