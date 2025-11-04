package jpamb.cases;

import jpamb.utils.Case;

public class CustomClasses {

    @Case("() -> assertion error")
    public static void assertFalse() {
        assert false;
    }

    static class PositiveInteger {
        private int value;

        PositiveInteger(int value) { set(value); }

        void set(int newValue) {
            if (newValue < 0) throw new IllegalArgumentException();
            this.value = newValue;
        }

        int get() { return value; }
    }   

    @Case("() -> ok")
    public static void Withdraw() {

        PositiveInteger balance = new PositiveInteger(1000);

        // assert balance.get() != 0;                  // suggested assertion
        // assert balance.get() - amount.get() >= 0;   // useful assertion
        // assert balance.get() > 10;                  // useless assertion
        // assert amount.get() + 10 > amount.get();    // tautology
        // assert balance.set(0) >= -1;                // wrong (side effect)
        // // ...
        // int percentageWithdrawn = amount.get() * 100 / balance.get();
        // balance.get() -= amount.get();
        return;
    }

}