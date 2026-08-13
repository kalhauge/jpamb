package jpamb;

import java.lang.reflect.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.*;
import java.util.stream.Stream;

import jpamb.utils.*;
import jpamb.utils.CaseContent.ResultType;
import jpamb.utils.InputParser.ParseError;
import jpamb.cases.*;

/**
 * The runtime method runs a single test-case and print the result or the
 * exeception.
 */
public class Runtime {
  static List<Class<?>> caseclasses = List.of(
      Simple.class,
      Loops.class,
      Tricky.class,
      jpamb.cases.Arrays.class,
      jpamb.cases.Strings.class,
      Dependent.class,
      Calls.class);

  public static Case[] cases(Method m) {
    var cases = m.getAnnotation(Cases.class);
    if (cases == null) {
      var c = m.getAnnotation(Case.class);
      if (c == null)
        return new Case[] {};
      return new Case[] { c };
    } else {
      return cases.value();
    }
  }

  public static void printType(Class<?> c, StringBuilder b) {
    if (c.equals(void.class)) {
      b.append("V");
    } else if (c.equals(int.class)) {
      b.append("I");
    } else if (c.equals(boolean.class)) {
      b.append("Z");
    } else if (c.equals(double.class)) {
      b.append("D");
    } else if (c.equals(float.class)) {
      b.append("F");
    } else if (c.equals(char.class)) {
      b.append("C");
    } else if (c.equals(int[].class)) {
      b.append("[I");
    } else if (c.equals(char[].class)) {
      b.append("[C");
    } else if (c.equals(String.class)) {
      b.append("Ljava/lang/String;");
    } else {
      throw new RuntimeException("Unknown type:" + c.toString());
    }
  }

  public static String printMethodSignature(Method m) {
    StringBuilder b = new StringBuilder();
    b.append("(");
    for (Class<?> c : m.getParameterTypes()) {
      printType(c, b);
    }
    b.append(")");
    printType(m.getReturnType(), b);
    return b.toString();
  }

  public static Class<?>[] parseMethodSignature(String s) {
    List<Class<?>> params = new ArrayList<>();
    for (int i = 0; i < s.length(); i++) {
      switch (s.charAt(i)) {
        case 'I' -> {
          params.add(int.class);
          break;
        }
        case 'Z' -> {
          params.add(boolean.class);
          break;
        }
        case 'C' -> {
          params.add(char.class);
          break;
        }
        case 'L' -> {
          i += 1;
          var start = i;
          while (i < s.length()) {
            if (s.charAt(i) == ';') {
              var str = s.substring(start, i);
              if (str.equals("java/lang/String")) {
                params.add(String.class);
                break;
              }
              throw new InputParser.ParseError("Invalid type", str);
            }
            i += 1;
          }
          break;
        }
        case '[' -> {
          i += 1;
          switch (s.charAt(i)) {
            case 'I' -> {
              params.add(int[].class);
              break;
            }
            case 'Z' -> {
              params.add(boolean[].class);
              break;
            }
            case 'C' -> {
              params.add(char[].class);
              break;
            }
          }
        }
      }
    }
    Class<?>[] rparams = new Class<?>[params.size()];
    params.toArray(rparams);

    return rparams;
  }

  public static void main(String[] args)
      throws ClassNotFoundException, NoSuchMethodException, IllegalAccessException {
    if (args.length == 0) {
      var mths = caseclasses.stream().flatMap(c -> Stream.of(c.getMethods())).toList();
      for (Method m : mths) {
        for (Case c : cases(m)) {
          CaseContent content = CaseContent.parse(c.value());
          String sig = printMethodSignature(m);
          String id = m.getDeclaringClass().getName() + "." + m.getName() + ":" + sig;
          if (!Modifier.isStatic(m.getModifiers())) {
            throw new RuntimeException("Expected " + id + " to be static");
          }
          System.out.printf("%-60s %s%n", id, content);
        }
      }
      return;
    }
    String thecase = args[0];
    Pattern pattern = Pattern.compile("(.*)\\.([^.(]*):\\((.*)\\)(.*)");
    Matcher matcher = pattern.matcher(thecase);
    if (matcher.find()) {
      String cls = matcher.group(1);
      String mth = matcher.group(2);
      String prams = matcher.group(3);
      System.err.printf("Found method %s in %s with %s%n", mth, cls, prams);
      Method m = Class.forName(cls).getMethod(mth, parseMethodSignature(prams));
      if (!Modifier.isStatic(m.getModifiers())) {
        throw new RuntimeException("Expected " + pattern + " to be static");
      }
      for (int i = 1; i < args.length; i++) {
        Object[] params = InputParser.parse(args[i]);
        System.err.printf("Running %s with %s%n", m, Arrays.toString(params));
        try {
          m.invoke(null, params);
        } catch (InvocationTargetException e) {
          System.out.println(ResultType.fromThrowable(e.getCause()));
          return;
        }
      }
      System.out.println(ResultType.SUCCESS);
    }
  }
}
