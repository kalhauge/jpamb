package jpamb.cases;

import jpamb.utils.Case;

public class Fuzzer{

  // Testing Constant Extraction fro strings lietrals and integers
    @Case("(0, s'other') -> ok")
    @Case("(1339, s'other') -> assertion error")
    @Case("(0, s'fuzz') -> assertion error")
    public static void fuzzConstant(int value, String name) {
    if (value == 1339) {
        assert false;
        }

    if ("fuzz".equals(name)) {
        assert false;
        }
    }

  // Boundary values - only one exact value triggers teh assertion

    @Case("(4096) -> ok")
    @Case("(4097) -> assertion error")
    @Case("(4098) -> ok")
    public static void fuzzBoundary(int value) {
        if (value > 4096) {
        if (value < 4098) {
            assert false;
        }
        }
    }

  // The compared target depends on another argument.
  // For base = 100, the runtime comparison exposes 3017.
  @Case("(100, 0) -> ok")
  @Case("(100, 3017) -> assertion error")
  @Case("(100, 3018) -> ok")
  public static void fuzzRuntimeComparison(int base, int candidate) {
    if (base < 100) {
      return;
    }
    if (base > 1000) {
      return;
    }

    int target = base * 30 + 17;
    if (candidate == target) {
      assert false;
    }
  }

    // Coverage - satisfied condition opens another branch (Retain partial progress)
    @Case("(0, 0, 0) -> ok")
    @Case("(31337, 0, 0) -> ok")
    @Case("(31337, -27183, 0) -> ok")
    @Case("(31337, -27183, 65521) -> assertion error")
    public static void fuzzCoverage(int first, int second, int third) {
    if (first == 31337) {
        if (second == -27183) {
        if (third == 65521) {
            assert false;
        }
        }
    }
    }

    // Runtime instrumentation
    @Case("(0, 400, 12014) -> ok")
    @Case("(24691, 0, 0) -> ok")
    @Case("(24691, 400, 12013) -> ok")
    @Case("(24691, 400, 12014) -> assertion error")
    @Case("(24691, 400, 12015) -> ok")
    public static void fuzzCombinedGuidance(
        int gate, int base, int candidate) {
    if (gate != 24691) {
        return;
    }
    if (base < 400) {
        return;
    }
    if (base > 900) {
        return;
    }

    int target = base * 30 + 13;
    if (candidate > target) {
        if (candidate < target + 2) {
        assert false;
        }
    }
    }
}