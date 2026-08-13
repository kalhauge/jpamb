package jpamb.cases;

import static jpamb.utils.Tag.TagType.*;

import jpamb.utils.*;

public class Arrays {

  @Case("() -> out of bounds")
  @Tag({ARRAY})
  public static void arrayOutOfBounds() {
    int array[] = {0, 0};
    array[3] = 0;
  }

  @Case("() -> ok")
  @Tag({ARRAY})
  public static void arrayInBounds() {
    int array[] = {0, 0};
    array[1] = 1;
  }

  @Case("() -> ok")
  @Tag({ARRAY})
  public static void arrayLength() {
    int array[] = {0, 0};
    assert array.length == 2;
  }

  @Case("() -> null pointer")
  @Tag({ARRAY})
  public static void arrayIsNull() {
    int array[] = null;
    array[1] = 10;
  }

  @Case("() -> null pointer")
  @Tag({ARRAY})
  public static void arrayIsNullLength() {
    int array[] = null;
    assert array.length == 0;
  }

  @Case("(11) -> null pointer")
  @Case("(0) -> out of bounds")
  @Tag({ARRAY})
  public static void arraySometimesNull(int i) {
    int array[] = null;
    if (i < 10) {
      array = new int[] {i};
    }
    array[1] = 10;
  }

  @Case("() -> assertion error")
  @Tag({ARRAY})
  public static void arrayContent() {
    int array[] = {1, 2, 100, -13, 23};
    for (int i = 0; i < array.length; i++) {
      assert i > 0;
    }
  }

  @Case("(3) -> ok")
  @Case("(6) -> assertion error")
  @Tag({ARRAY})
  public static void binarySearch(int x) {
    int arr[] = {2, 3, 4, 10, 40};
    int l = 0, r = arr.length - 1;
    while (l <= r) {
      int m = l + (r - l) / 2;
      if (arr[m] == x) return;
      if (arr[m] < x) l = m + 1;
      else r = m - 1;
    }
    assert false;
  }

  @Case("([I: ]) -> assertion error")
  @Case("([I: 1]) -> ok")
  @Tag({ARRAY})
  public static void arrayNotEmpty(int[] array) {
    assert array.length > 0;
  }

  @Case("([C: 'h','e','l','l','o']) -> ok")
  @Case("([C: 'x']) -> assertion error")
  @Case("([C: ]) -> out of bounds")
  @Tag({ARRAY})
  public static void arraySpellsHello(char[] array) {
    assert array[0] == 'h'
        && array[1] == 'e'
        && array[2] == 'l'
        && array[3] == 'l'
        && array[4] == 'o';
  }

  @Case("([I: 50, 100, 200]) -> ok")
  @Case("([I: ]) -> assertion error")
  @Tag({ARRAY})
  public static void arraySumIsLarge(int[] array) {
    int sum = 0;
    for (int i = 0; i < array.length; i++) {
      sum += array[i];
    }
    assert sum > 300;
  }
}
