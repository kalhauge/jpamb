package jpamb.cases;

import jpamb.utils.Case;

import jpamb.cases.PositiveInteger;
import jpamb.cases.BooleanTrue;

public class CustomClasses {

    @Case("() -> assertion error")
    public static void assertFalse() {
        assert false;
    }

    static class ClassInputTest{

        private PositiveInteger pi;

        ClassInputTest(PositiveInteger new_pi) {this.pi = new_pi;}
    }

    @Case("(5) -> ok")
    public static void WithdrawInt(int i) {
        PositiveInteger amount = new PositiveInteger(i);

        // int a = 2;
        return;
    }

    @Case("(new jpamb/cases/BooleanTrue(true)) -> ok")
    public static void WithdrawBooleanTrue(BooleanTrue b) {
        

        return;
    }

    @Case("(new jpamb/cases/PositiveInteger(5)) -> ok")
    public static void Withdraw(PositiveInteger amount) {

        PositiveInteger balance = new PositiveInteger(1000);

        // int new_value = amount.get();
        // int a = 2;
        // BooleanTrue b_test = new BooleanTrue(true);
        // ClassInputTest class_test = new ClassInputTest(balance);     -> overkill

        // assert balance.get() != 0;                  // suggested assertion
        assert balance.get() - amount.get() >= 0;   // useful assertion
        // assert balance.get() > 10;                  // useless assertion
        // assert amount.get() + 10 > amount.get();    // tautology
        // assert balance.set(0) >= -1;                // wrong (side effect)
        // // ...
        // int percentageWithdrawn = amount.get() * 100 / balance.get();
        // balance.get() -= amount.get();
        return;
    }

}