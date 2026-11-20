package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Tag;

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

  @Case("(24) -> assertion error")
  @Case("(0) -> ok")
  @Tag({LOOP})
  public static void loopDoubling(int n) {
    int acc = n;
    for (int i = 0; i < 4; i++) {
      acc = acc * 2 + 1;
    }
    assert acc != 399;
  }

  @Case("(71, 29) -> divide by zero")
  @Case("(50, 50) -> ok")
  @Tag({CONDITIONAL})
  public static int twoParams(int a, int b) {
    if (a + b == 100) {
      return 1 / (a - b - 42);
    }
    return 0;
  }

  @Case("(0) -> out of bounds")
  @Case("(999993) -> divide by zero")
  @Case("(999990) -> ok")
  @Tag({ARRAY})
  public static int tableLookup(int i) {
    int[] table = {4, 8, 15, 16, 23, 42};
    return 100 / (table[i - 999990] - 16);
  }

  @Case("(24) -> ok")
  @Tag({LOOP})
  public static void loopDoublingSafe(int n) {
    int acc = n;
    for (int i = 0; i < 4; i++) {
      acc = acc * 2 + 1;
    }
    assert acc != 400;
  }

  @Case("(71, 29) -> ok")
  @Tag({CONDITIONAL})
  public static int twoParamsSafe(int a, int b) {
    if (a + b == 100) {
      return 1 / (a - b - 43);
    }
    return 0;
  }

  @Case("(999993) -> ok")
  @Tag({ARRAY, CONDITIONAL})
  public static int tableLookupSafe(int i) {
    int[] table = {4, 8, 15, 17, 23, 42};
    if (i < 999990 || i > 999995) {
      return 0;
    }
    return 100 / (table[i - 999990] - 16);
  }

  @Case("(123456789) -> assertion error")
  @Case("(123456788) -> ok")
  public static void narrowEquality(int n) {
    assert n != 123456789;
  }

  @Case("(1005) -> assertion error")
  @Case("(1004) -> ok")
  public static void rangeCondition(int n) {
    if (n >= 1000 && n <= 1010) {
      assert n != 1005;
    }
  }

  @Case("(40) -> assertion error")
  @Case("(39) -> ok")
  public static void loopAndEquality(int n) {
    for (int i = 0; i < 3; i++) {
      n += 10;
    }
    assert n != 70;
  }

  @Case("(101) -> ok")
  public static void unreachableRange(int n) {
    if (n > 100 && n < 50) {
      assert false;
    }
  }
}
