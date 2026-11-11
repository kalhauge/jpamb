package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.Case;
import jpamb.utils.Tag;

public class Group25 {

  @Case("(0) -> ok")
  @Case("(20) -> ok")
  @Case("(500) -> ok")
  @Tag({CONDITIONAL})
  public static int pageSize(int requested) {
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
  public static int pageCount(int items, int requested) {
    assert items >= 0;
    int size = pageSize(requested);
    int pages = items / size;
    if (items % size != 0) {
      pages++;
    }
    return pages;
  }

  @Case("(0, 95, 10) -> ok")
  @Case("(9, 95, 10) -> ok")
  @Case("(10, 95, 10) -> assertion error")
  @Case("(0, -1, 10) -> assertion error")
  @Tag({CALL, CONDITIONAL})
  public static int itemsOnPage(int page, int items, int requested) {
    int pages = pageCount(items, requested);
    assert page >= 0 && page < pages;
    int size = pageSize(requested);
    if (page == pages - 1 && items % size != 0) {
      return items % size;
    }
    return size;
  }

  @Case("(95, 10) -> ok")
  @Case("(100, 10) -> ok")
  @Case("(0, 10) -> assertion error")
  @Tag({CALL})
  public static int lastPageItems(int items, int requested) {
    int pages = pageCount(items, requested);
    return itemsOnPage(pages - 1, items, requested);
  }

  @Case("([I:]) -> ok")
  @Case("([I:1, 2, 3]) -> ok")
  @Tag({ARRAY, LOOP})
  public static int[] prefixSums(int[] xs) {
    int[] sums = new int[xs.length + 1];
    for (int i = 0; i < xs.length; i++) {
      sums[i + 1] = sums[i] + xs[i];
    }
    return sums;
  }
}
