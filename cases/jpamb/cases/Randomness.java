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

    

    public static boolean coinflip() {
        return Math.random()>0.5; //preliminary value 
    }

}
