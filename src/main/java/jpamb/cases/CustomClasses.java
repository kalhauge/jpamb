package jpamb.cases;

import jpamb.utils.Case;

public class CustomClasses {

  @Case("() -> assertion error")
  public static void assertFalse() {
    assert false;
  }
}