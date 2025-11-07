package jpamb.cases;

import jpamb.utils.Case;


public class BooleanTrue {
        private boolean value;

        BooleanTrue(boolean value) { set(value); }

        void set(boolean newValue) {
            if (newValue != true) throw new IllegalArgumentException();
            this.value = newValue;
        }

        boolean get() { return value; }
}   