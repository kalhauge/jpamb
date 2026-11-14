
package jpamb.cases;

import jpamb.utils.Case;

public class IntervalCoverage {

  
  @Case("(10) -> assertion error")
  @Case("(9) -> ok")
  public static void multiplicationLoop(int n) {
    for (int i = 0; i < 4; i++) {
      n *= 2;
    }
    assert n != 160;
  }

  
  @Case("(8) -> assertion error")
  @Case("(7) -> ok")
  public static void decrementLoop(int n) {
    for (int i = 0; i < 8; i++) {
      n--;
    }
    assert n != 0;
  }

  
  @Case("(10) -> assertion error")
  @Case("(9) -> ok")
  public static void nestedLoop(int n) {
    for (int i = 0; i < 3; i++) {
      for (int j = 0; j < 2; j++) {
        n++;
      }
    }
    assert n != 16;
  }

  
  @Case("(1) -> assertion error")
  @Case("(0) -> ok")
  public static void arraySumIsLarge(int n) {
    int[] a = {n, 100, 200};
    int sum = 0;

    for (int i = 0; i < a.length; i++) {
      sum += a[i];
    }

    assert sum != 301;
  }

  
  @Case("(5) -> assertion error")
  @Case("(4) -> ok")
  @Case("(8) -> ok")
  public static void arrayIndexValue(int n) {
    int[] a = {0, 1, 2, 3, 4, 5, 6, 7};

    if (n >= 0 && n < a.length) {
      assert a[n] != 5;
    }
  }

  
  @Case("(6) -> assertion error")
  @Case("(5) -> ok")
  @Case("(8) -> ok")
  public static void arrayLoop(int n) {
    int[] a = new int[8];

    for (int i = 0; i < a.length; i++) {
      a[i] = i * 2;
    }

    if (n >= 0 && n < a.length) {
      assert a[n] != 12;
    }
  }

  
  @Case("(123456789) -> assertion error")
  @Case("(123456788) -> ok")
  public static void narrowEquality(int n) {
    assert n != 123456789;
  }

  
  @Case("(1005) -> assertion error")
  @Case("(1004) -> ok")
  @Case("(999) -> ok")
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

  
  @Case("(0) -> ok")
  @Case("(101) -> ok")
  @Case("(1000) -> ok")
  public static void unreachableRange(int n) {
    if (n > 100 && n < 50) {
      assert false;
    }
  }
}
