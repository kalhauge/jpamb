# S-Expressions

An S-Expression is a compact way to represent data. Values are either **symbols** (strings) or **lists** of items and **keyed options**.

For example:

```
(foo bar :baz qux)         ; -> ("foo", "bar", baz="qux")
```

- A **symbol** is a bare token, or a double-quoted string to allow spaces/escapes (`"my symbol"`).
- A **list** is a pair of parentheses containing expressions.
- A **keyword** starts with `:` (e.g., `:baz`) and binds the following expression as a keyed **option**, making lists usable as records: the first element is conventionally a tag or name, followed by positional items and `:key value` pairs.

## In Python

`src/sexpr.py` implements a sexpr dialect:

### Parsing and Printing

```python
from sexpr import from_string, pretty

parse = from_string('(foo bar :baz qux)')   # list of SExpr
pretty(parse[0])                           # 'foo bar :baz qux'
```

### Building and Converting

`sexpr(...)` converts Python values (dicts, lists, `None`, numbers) into sexprs; `data(name, *args, **kwargs)` builds tagged data structures; `from_sexpr(expr, target=...)` decodes sexrs back into typed Python values, including dataclasses (tagged via `sexprtag`) and tagged unions.
