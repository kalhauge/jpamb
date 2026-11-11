package jpamb.cases;
import jpamb.utils.Case;

public class Group25 {

  @Case("(0) -> ok")
  @Case("(20) -> ok")
  @Case("(500) -> ok")
  public static int pageSizeRev0(int requested) {
    if (requested <= 0) {
      return 10;
    }
    if (requested > 50) {
      return 50;
    }
    return requested;
  }
}