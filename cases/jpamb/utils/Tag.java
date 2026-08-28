package jpamb.utils;

import java.lang.annotation.*;

// Annotation for tagging methods
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Tag {
  TagType[] value();

  public static enum TagType {
    CONDITIONAL,
    LOOP,
    INTEGER_OVERFLOW,
    CALL,
    ARRAY,
    RECURSION,
    STDLIB,
  }
}
