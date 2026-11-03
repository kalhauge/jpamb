package jpamb.utils;

public final class Bitstring {
    private final String bits;

    public Bitstring(String bits) {
        for (int i = 0; i < bits.length(); i++) {
            char bit = bits.charAt(i);

            if (bit != '0' && bit != '1') {
                throw new IllegalArgumentException(
                    "A bitstring can only contain 0 and 1"
                );
            }
        }

        this.bits = bits;
    }

    public char bitAt(int index) {
        return bits.charAt(index);
    }

    public int length() {
        return bits.length();
    }

    @Override
    public String toString() {
        return bits;
    }
}