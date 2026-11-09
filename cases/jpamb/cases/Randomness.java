package jpamb.cases;
//import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Smith;

public class Randomness {

    
    @Case( "(r'01010101') -> assertion error") 
    @Case( "(r'100000') -> ok") 
    public static void randomBranch(Smith smith) {
        if (smith.draw()) {
            assert true;
        } else {
            assert false;
        }
    }

    @Case("(r'11') -> assertion error")
    @Case("(r'10') -> ok")
    @Case("(r'01') -> ok")
    @Case("(r'00') -> ok")
    public static void twoDraws(Smith smith) {
        boolean first = smith.draw();
        boolean second = smith.draw();
        assert !(first && second);
    }

    @Case("(0, r'1') -> divide by zero")
    @Case("(0, r'0') -> ok")
    @Case("(2, r'1') -> ok")
    public static int drawDependsOnArg(int n, Smith smith) {
        return smith.draw() ? 1 / n : 0;
    }

    @Case("(r'1') -> ok")
    @Case("(r'0001') -> ok")
    @Case("(r'00001') -> assertion error")
    public static void loopUntilHeads(Smith smith) {
        int tails = 0;
        while (!smith.draw()) {
            tails++;
        }
        assert tails <= 3;
    }

    @Case("(r'1') -> ok")
    @Case("(r'0') -> *")
    public static void spinOnTails(Smith smith) {
        if (!smith.draw()) {
            while (true) {}
        }
    }

    @Case("(r'0') -> ok")
    @Case("(r'1') -> out of bounds")
    public static void randomIndex(Smith smith) {
        int[] array = new int[1];
        int index = smith.draw() ? 1 : 0;
        array[index] = 1;
    }

    @Case("(r'1') -> ok")
    @Case("(r'0') -> null pointer")
    public static void randomNull(Smith smith) {
        int[] array = smith.draw() ? new int[1] : null;
        array[0] = 1;
    }

    private static boolean heads(Smith smith) {
        return smith.draw();
    }

    @Case("(r'1') -> ok")
    @Case("(r'0') -> assertion error")
    public static void drawInCallee(Smith smith) {
        assert heads(smith);
    }

    @Case("(r'1') -> assertion error")
    @Case("(r'000010000000001') -> ok")
    @Case("(r'1100010101110101011101010') -> ok")
    @Case("(r'000010000000000') -> divide by zero")
    public static void drawInt(Smith smith) {
        try {
            int value = smith.draw(4);
        } catch (IllegalStateException e) {
            assert false;
        }

        if (value >= 5) {
            1/smith.draw(10);
        }
    }
    
}
