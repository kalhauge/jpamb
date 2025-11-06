package jpamb.cases;

import jpamb.utils.Case;


public class PositiveInteger {

        private int value;

        PositiveInteger(int value) { set(value); }

        void set(int newValue) {
            if (newValue < 0) throw new IllegalArgumentException();
            this.value = newValue;
        }

        int get() { return value; }
}   