package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.*;

public class Tricky {

  @Case("(0) -> assertion error")
  @Case("(24) -> ok")
  @Tag({LOOP})
  public static void collatz(int n) {
    assert n > 0;
    while (n != 1) {
      if (n % 2 == 0) {
        n = n / 2;
      } else {
        n = n * 3 + 1;
      }
    }
  }
}
