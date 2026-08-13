package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.*;

public class Loops {

  @Case("() -> *")
  @Tag({LOOP})
  public static void forever() {
    while (true) {}
  }

  @Case("() -> *")
  @Tag({LOOP})
  public static void neverAsserts() {
    int i = 1;
    while (i > 0) {}
    assert false;
  }

  @Case("() -> *")
  @Tag({LOOP})
  public static int neverDivides() {
    int i = 1;
    while (i > 0) {}
    return 0 / 0;
  }

  @Case("() -> assertion error")
  @Tag({LOOP, INTEGER_OVERFLOW})
  public static void terminates() {
    short i = 0;
    while (i++ != 0) {}
    assert false;
  }
}
