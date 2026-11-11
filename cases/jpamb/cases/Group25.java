package jpamb.cases;
import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Tag;

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

  @Case("(0, 10) -> ok")
  @Case("(95, 10) -> ok")
  @Case("(-1, 10) -> assertion error")
  @Tag({CALL, CONDITIONAL})
  public static int pageCountRev0(int items, int requested) {
    assert items >= 0;
    int size = pageSizeRev0(requested);
    int pages = items / size;
    if (items % size != 0) {
      pages++;
    }
    return pages;
  }
}