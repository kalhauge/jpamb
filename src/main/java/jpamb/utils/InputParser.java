package jpamb.utils;

import java.util.ArrayList;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class InputParser {
  private Scanner sc;
  private String currentToken;
  private final String input;

  public static class ParseError extends RuntimeException {
    public ParseError(String err, String input) {
      super(err + " in " + input);
    }
  }

  public InputParser(String input) {
    this.input = input;
    sc = new Scanner(input);
    sc.useDelimiter("\\s*");
    nextToken();
  }

  private void nextToken() {
    if (sc.hasNext()) {
      currentToken = sc.findWithinHorizon(
          "[-]?[0-9\\.]+|\\[[ICZ]:|\\(|\\)|\\]|,|s?'[^']*'|true|false", 0);
    } else {
      currentToken = null;
    }
  }

  private void expect(String expected) {
    if (!expected.equals(currentToken)) {
      expected(expected);
    }
    nextToken();
  }

  public static Object[] parse(String inputs) {
    return new InputParser(inputs).parseInputs();
  }

  private Object parseInput() {
    if (currentToken.matches("[-]?[0-9]+")) {
      int value = Integer.parseInt(currentToken);
      nextToken();
      return value;
    } else if (currentToken.matches("'[^']'")) {
      var chr = currentToken.charAt(1);
      nextToken();
      return chr;
    } else if (currentToken.matches("s'[^']*'")) {
      var string = currentToken.substring(2, currentToken.length() - 1);
      nextToken();
      return string;
    } else if (currentToken.equals("true")) {
      nextToken();
      return true;
    } else if (currentToken.equals("false")) {
      nextToken();
      return false;
    } else if (currentToken.equals("[I:")) {
      return parseIntList();
    } else if (currentToken.equals("[C:")) {
      return parseCharList();
    } else {
      expected("input");
      return null;
    }
  }

  private void expected(String expected) {
    throw new ParseError("Expected " + expected + " but got '" + currentToken + "'", input);
  }

  private Object parseIntList() {
    ArrayList<Integer> items = new ArrayList<>();
    expect("[I:");

    if (currentToken == null)
      expected("integer or ]");

    if (currentToken.equals("]")) {
      nextToken();
      return new int[] {};
    }

    if (!currentToken.matches("[0-9]+"))
      expected("integer");

    items.add(Integer.parseInt(currentToken));
    nextToken();

    while (currentToken != null && currentToken.equals(",")) {
      nextToken();
      if (currentToken == null || !currentToken.matches("[0-9]+"))
        expected("integer");
      items.add(Integer.parseInt(currentToken));
      nextToken();
    }

    expect("]");

    int[] output = new int[items.size()];
    for (int i = 0; i < items.size(); i++) {
      output[i] = items.get(i);
    }
    return output;
  }

  private Object parseCharList() {
    ArrayList<Character> items = new ArrayList<>();
    expect("[C:");

    if (currentToken == null)
      expected("char or ]");

    if (currentToken.equals("]")) {
      nextToken();
      return new char[] {};
    }

    if (!currentToken.matches("'[^']+'"))
      expected("char");

    items.add(currentToken.charAt(1));
    nextToken();

    while (currentToken != null && currentToken.equals(",")) {
      nextToken();
      if (currentToken == null || !currentToken.matches("'[^']+'"))
        expected("char");
      items.add(currentToken.charAt(1));
      nextToken();
    }

    expect("]");

    char[] output = new char[items.size()];
    for (int i = 0; i < items.size(); i++) {
      output[i] = items.get(i);
    }
    return output;
  }

  private Object[] parseInputs() {
    ArrayList<Object> list = new ArrayList<>();

    expect("(");

    if (currentToken == null)
      expected("input or )");

    if (currentToken.equals(")")) {
      nextToken();
      return new Object[] {};
    }

    list.add(parseInput());

    while (currentToken != null && currentToken.equals(",")) {
      nextToken();
      list.add(parseInput());
    }

    expect(")");
    return list.toArray();
  }

}
