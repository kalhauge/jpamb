package jpamb.utils;

public final class Bitstring implements BitVector {
  private final String bits;

  public Bitstring(String bits) {
    for (int i = 0; i < bits.length(); i++) {
      char bit = bits.charAt(i);

      if (bit != '0' && bit != '1') {
        throw new IllegalArgumentException("A bitstring can only contain 0 and 1");
      }
    }

    this.bits = bits;
  }

  @Override
  public int length() {
    return bits.length();
  }

  @Override
  public boolean bitAt(int index) {
    if (index < 0 || index >= bits.length()) {
      throw new IndexOutOfBoundsException(index);
    }
    return bits.charAt(index) == '1';
  }

  @Override
  public String toString() {
    return bits;
  }
}
