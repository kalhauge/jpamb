package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.*;

public class Overflow {

  // Looks safe: n >= 0, so 1 <= n + 1 < 4. But n + 1 wraps around
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
}
