package jpamb.utils;

import java.lang.annotation.*;

@Repeatable(Cases.class)
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Case {
  String value();
}
