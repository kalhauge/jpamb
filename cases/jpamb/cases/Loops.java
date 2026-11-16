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


}
