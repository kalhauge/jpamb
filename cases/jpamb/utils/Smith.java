package jpamb.utils;

public interface Smith {
    public boolean draw(); 
}

final class BitSmith implements Smith {
    private final String bits;
    private int index;

    BitSmith(String bits) {
        this.bits = bits;
    }

    String bits() {
        return bits;
    }

    @Override
    public boolean draw() {
        if (index >= bits.length()) {
            throw new IllegalStateException("Smith input exhausted");
        }
        return bits.charAt(index++) != '0';
    }
}
