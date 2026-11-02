package jpamb.cases;

import jpamb.utils.Case;

public class Strings {

  @Case("(s'hello') -> ok")
  @Case("(s'not hello') -> assertion error")
  public static void sayHello(String greeting) {
    assert greeting.equals("hello");
  }

  @Case("(s'good morning') -> ok")
  @Case("(s'morning') -> assertion error")
  public static void sayHello2(String greeting) {
    assert (greeting.startsWith("good"));
    assert greeting.contains("morning");
  }

  @Case("(s'good morning') -> assertion error")
  @Case("(s'bad night') -> ok")
  public static void sayHello3(String greeting) {
    assert !(greeting.startsWith("good"));
    assert (greeting.endsWith("night"));
  }

  @Case("(s'document.pdf') -> ok")
  @Case("(s'.pdf') -> assertion error")
  @Case("(s'document.doc') -> assertion error")
  public static void checkExtension(String filename) {
    assert filename.endsWith(".pdf");
    assert !filename.startsWith(".");
  }

  @Case("(s'A---B---Z') -> ok")
  @Case("(s'A------Z') -> assertion error")
  @Case("(s'B------Z') -> assertion error")
  @Case("(s'A---B---X') -> assertion error")
  public static void checkComplexSequence(String text) {
    assert text.startsWith("A");
    assert text.endsWith("Z");
    assert text.contains("B");
  }
}
