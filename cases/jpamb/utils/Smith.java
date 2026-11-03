package jpamb.utils;

public interface Smith {
    public boolean draw(); 
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
}
 