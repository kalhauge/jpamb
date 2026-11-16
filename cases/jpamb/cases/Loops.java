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

  @Case("(0, 0) -> ok")
  @Case("(0, 1) -> divide by zero")
  public static int forLoopDivision(int divisor, int iterations) {
    int result = 100;
    for (int i = 0; i < iterations; i++) result /= divisor;
    return result;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 2) -> divide by zero")
  public static int whileLoopDivision(int divisor, int iterations) {
    int result = 100;
    int i = 0;
    while (i < iterations) {
      result /= divisor;
      i++;
    }
    return result;
  }

  @Case("(0, 0) -> divide by zero")
  @Case("(2, 0) -> ok")
  public static int doWhileDivision(int divisor, int iterations) {
    int result = 100;
    int i = 0;
    do {
      result /= divisor;
      i++;
    } while (i < iterations);
    return result;
  }

  @Case("(0, 0) -> ok")
  @Case("(0, 1) -> divide by zero")
  public static int loopRemainder(int divisor, int iterations) {
    int result = 100;
    for (int i = 0; i < iterations; i++) result %= divisor;
    return result;
  }

  // below inlcude a bit complex cases for the analyzer
  @Case("(0, 5, 0) -> ok")
  @Case("(1, 21, 3) -> ok")
  // Tests whether the analyzer handles division and modulo safely
  // inside nested if-else branches with zero checks.
  public static int safeNestedBranchDivision(int mode, int value, int divisor) {
    if (mode > 0) {
      if (divisor == 0) return value;
      return value / divisor;
    }
    if (mode < 0) {
      if (divisor == 0) return -value;
      return value % divisor;
    }
    return 0;
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
