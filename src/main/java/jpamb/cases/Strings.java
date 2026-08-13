package jpamb.cases;

import jpamb.utils.Case;

public class Strings {

  @Case("(s'hello') -> ok")
  @Case("(s'not hello') -> assertion error")
  public static void sayHello(String greeting) {
    assert greeting.equals("hello");
  }

}
