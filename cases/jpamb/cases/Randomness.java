package jpamb.cases;
//import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Smith;

public class Randomness {

    
    @Case( "(b'102313312') -> assertion error") 
    @Case( "(b'12312') -> ok") 
    public static void randomBranch(Smith smith) {
        if (smith.draw()) {
            assert true;
        } else {
            assert false;
        }
    }

    

    public static boolean coinflip() {
        return Math.random()>0.5; //preliminary value 
    }

}

