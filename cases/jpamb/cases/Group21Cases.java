package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Tag;

// Benchmark methods added by Group 21.
public class Group21Cases {

  // Bastian: safe, but the loop condition is '!=' instead of '<'. An interval
  // cannot exclude a single value in the middle, so an analysis that widens i
  // to "any non-negative int" can no longer recover the bound 8.
  @Case("() -> ok")
  @Tag({ARRAY, LOOP})
  public static void arrayFillUntilEqual() {
    int array[] = new int[8];
    for (int i = 0; i != 8; i++) {
      array[i] = i;
    }
  }

  // Bastian: looks safe: n >= 0, so 1 <= n + 1 < 4. But n + 1 wraps around
  // due to integer overflow.
  @Case("(0) -> ok")
  @Case("(2147483647) -> out of bounds")
  @Tag({ARRAY, INTEGER_OVERFLOW})
  public static int arrayIndexAfterOverflow(int n) {
    int array[] = new int[4];
    if (n >= 0) {
      int i = n + 1;
      if (i < 4) {
        return array[i];
      }
    }
    return 0;
  }

  // Chris: the assertion is unreachable because n * 2 is always even.
  @Case("(7) -> ok")
  @Case("(-3) -> ok")
  public static void unreachableAssert(int n) {
    int x = n * 2;
    if (x % 2 != 0) {
      assert false;
    }
  }

  // Christian: the division is only reached for the exact input "secret".
  @Case("([C: 's', 'e', 'c', 'r', 'e', 't']) -> divide by zero")
  @Case("([C: 's', 'e', 'c', 'r', 'e', 'x']) -> ok")
  @Case("([C:]) -> ok")
  @Tag({ARRAY})
  public static int secretThenDivide(char[] a) {
    if (a.length == 6 && a[0] == 's' && a[1] == 'e' && a[2] == 'c'
        && a[3] == 'r' && a[4] == 'e' && a[5] == 't') {
      return 1 / (a.length - 6);
    }
    return 0;
  }

 // Janus: the division only exists in the callee, so an analysis must
  // follow calls.

  public static int scale(int x, int d) {
    return x / d;
  }
 
  @Case("(3) -> divide by zero")
  @Case("(0) -> ok")
  @Tag({CALL})
  public static int divideViaHelper(int n) {
    return scale(100, n - 3);
  }
}
