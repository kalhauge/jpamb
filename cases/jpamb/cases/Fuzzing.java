package jpamb.cases;

import static jpamb.utils.Tag.TagType.ARRAY;

import jpamb.utils.Case;
import jpamb.utils.Tag;

public class Fuzzing {
  // The division is only reached for the exact input "secret".
  @Case("([C: 's', 'e', 'c', 'r', 'e', 't']) -> divide by zero")
  @Case("([C: 's', 'e', 'c', 'r', 'e', 'x']) -> ok")
  @Tag({ARRAY})
  public static int secretThenDivide(char[] a) {
    if (a.length == 6 && a[0] == 's' && a[1] == 'e' && a[2] == 'c'
        && a[3] == 'r' && a[4] == 'e' && a[5] == 't') {
      return 1 / (a.length - 6);
    }
    return 0;
  }
}
