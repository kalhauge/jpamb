package jpamb.utils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeoutException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public record CaseContent(
    Object[] params,
    ResultType result) {

  public String toString() {
    List<String> sparams = Arrays.asList(params).stream().map(CaseContent::toInputString).toList();
    return "(" + String.join(", ", sparams) + ") -> " + result.toString();
  }

  public static String toInputString(Object obj) {
    if (obj instanceof int[]) {
      return "[I:" + Arrays.toString((int[]) obj).substring(1);
    } else if (obj instanceof char[]) {
      List<String> chars = new ArrayList<>();
      for (char x : (char[]) obj) {
        chars.add("'" + x + "'");
      }
      return "[C:" + String.join(", ", chars) + "]";
    } else if (obj instanceof String) {
      return "s'" + obj + "'";
    } else {
      return obj.toString();
    }

  }

  public static CaseContent parse(String string) {
    Pattern pattern = Pattern.compile("(\\([^)]*\\))\\s*->\\s*(.+)");
    Matcher matcher = pattern.matcher(string);
    // Parse the expression
    if (matcher.find()) {
      String args = matcher.group(1);
      String result = matcher.group(2);
      return new CaseContent(InputParser.parse(args), ResultType.parse(result));
    } else {
      throw new RuntimeException("Invalid case: " + string);
    }
  }

  public static enum ResultType {
    DIVIDE_BY_ZERO,
    ASSERTION_ERROR,
    SUCCESS,
    NON_TERMINATION,
    NULL_POINTER,
    OUT_OF_BOUNDS;

    public static ResultType parse(String string) {
      if (string.equals("*")) {
        return NON_TERMINATION;
      } else if (string.equals("assertion error")) {
        return ASSERTION_ERROR;
      } else if (string.equals("out of bounds")) {
        return OUT_OF_BOUNDS;
      } else if (string.equals("null pointer")) {
        return NULL_POINTER;
      } else if (string.equals("divide by zero")) {
        return DIVIDE_BY_ZERO;
      } else if (string.equals("ok")) {
        return SUCCESS;
      } else {
        throw new RuntimeException("Invalid result type: " + string);
      }
    }

    public String toString() {
      switch (this) {
        case DIVIDE_BY_ZERO:
          return "divide by zero";
        case ASSERTION_ERROR:
          return "assertion error";
        case OUT_OF_BOUNDS:
          return "out of bounds";
        case NULL_POINTER:
          return "null pointer";
        case NON_TERMINATION:
          return "*";
        case SUCCESS:
          return "ok";
        default:
          throw new RuntimeException("Unexpected");
      }
    }

    public static ResultType fromThrowable(Throwable cause) {
      if (cause instanceof ArithmeticException) {
        return DIVIDE_BY_ZERO;
      } else if (cause instanceof AssertionError) {
        return ASSERTION_ERROR;
      } else if (cause instanceof TimeoutException) {
        return NON_TERMINATION;
      } else if (cause instanceof ArrayIndexOutOfBoundsException) {
        return OUT_OF_BOUNDS;
      } else if (cause instanceof NullPointerException) {
        return NULL_POINTER;
      } else {
        throw new RuntimeException("Unexpected");
      }
    }
  }
}
