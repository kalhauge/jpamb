package jpamb.cases;
//import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
//import jpamb.utils.Tag;
public class Randomness {
    
    @Case( "(1) -> assertion error") 
    @Case( "(2) -> ok") 
    public static void randomBranch(int dummy) {
        if (coinflip()) {
            assert true;
        } else {
            assert false;
        }
    }
    @Case("() -> ok")
    public static void assertTrue() {
        assert true;
    }

    public static boolean coinflip() {
        return true; //preliminary value 
    }


}

