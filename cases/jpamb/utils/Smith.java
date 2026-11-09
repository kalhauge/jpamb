package jpamb.utils;

public interface Smith {
    public boolean draw(); 
    public int draw(int bits);
}

final class BitSmith implements Smith {
    private final Bitstring bits;
    private int index;

    BitSmith(Bitstring bits) {
        this.bits = bits;
    }

    String bits() {
        return bits.toString();
    }

    @Override
    public boolean draw() {
        if (index >= bits.length()) {
            throw new IllegalStateException("Smith input exhausted");
        }
        return bits.bitAt(index++) != '0';
    }

    @Override
    public int draw(int bits) {
        if (index + bits >= this.bits.length()) {
            throw new IllegalStateException("Smith input exhausted");
        }
        int value = 0;
        for (int i = index; i < index + bits; i++) {
            value = (value << 1) | (this.bits.bitAt(i) == '0' ? 0 : 1);
        }
        index += bits;
        return value;
    }
}
 
