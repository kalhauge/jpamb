package jpamb.cases;

import jpamb.utils.Case;

public class BitOperations {
  @Case("(10, 10) -> assertion error")
  @Case("(4, 0) -> ok")
  public static void xor(int a, int b) {
    int val = a ^ b;
    assert val > 0;
  }

  @Case("(1) -> assertion error")
  @Case("(4) -> ok")
  public static void bitshiftLeft(int a) {
    int val = a << 4;
    assert val > 16;
  }

  @Case("(10000) -> assertion error")
  @Case("(128) -> ok")
  public static void bitshiftRight(int a) {
    int val = a >> 4;
    assert val < 64;
  }

  @Case("(10000, 4) -> assertion error")
  @Case("(128, 128) -> ok")
  public static void bitwiseAnd(int a, int b) {
    int val = a & b;
    assert val > 0;
  }

  @Case("(10000, 2) -> assertion error")
  @Case("(128, 3) -> ok")
  public static void bitwiseOr(int a, int b) {
    int val = a | b;
    assert val < 256;
  }

  @Case("(10000) -> assertion error")
  @Case("(128) -> ok")
  public static void bitwiseNot(int a) {
    int val = ~a;
    assert val > -256;
  }

  @Case("(4) -> assertion error")
  @Case("(32) -> ok")
  public static void drawInt(int count) {
    String bits =
        "10010101010101010101010110110101010100110101010101111000001010101010101110100111011001110101001001001";
    int value = 0;
    for (int i = 0; i < count; i++) {
      value = (value << 1) | (bits.charAt(i) == '0' ? 0 : 1);
    }
    assert value < 0 || value == 2;
  }

  @Case("(-1) -> assertion error")
  @Case("(128) -> ok")
  public static void bitshiftUnsignedRight(int a) {
    int val = a >>> 4;
    assert val < 64;
  }
}
