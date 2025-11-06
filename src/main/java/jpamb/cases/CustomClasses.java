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

    static class BooleanTrue {
        private boolean value;

        BooleanTrue(boolean value) { set(value); }

        void set(boolean newValue) {
            if (newValue != true) throw new IllegalArgumentException();
            this.value = newValue;
        }

        boolean get() { return value; }
    }   

    static class ClassInputTest{

        private PositiveInteger pi;

        ClassInputTest(PositiveInteger new_pi) {this.pi = new_pi;}
    }

    @Case("(5) -> ok")
    public static void WithdrawInt(int i) {
        PositiveInteger balance = new PositiveInteger(i);

    }

    @Case("(new PositiveInteger(5)) -> ok")
    public static void Withdraw(PositiveInteger amount) {

        PositiveInteger balance = new PositiveInteger(1000);

        int a = 2;
        // BooleanTrue b_test = new BooleanTrue(true);
        // ClassInputTest class_test = new ClassInputTest(balance);     -> overkill

        // assert balance.get() != 0;                  // suggested assertion
        //assert balance.get() - amount.get() >= 0;   // useful assertion
        // assert balance.get() > 10;                  // useless assertion
        // assert amount.get() + 10 > amount.get();    // tautology
        // assert balance.set(0) >= -1;                // wrong (side effect)
        // // ...
        // int percentageWithdrawn = amount.get() * 100 / balance.get();
        // balance.get() -= amount.get();
        return;
    }

}