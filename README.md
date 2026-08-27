# JPAMB: Java Program Analysis Micro Benchmarks

JPAMB is a collection of small Java programs with various behaviors (crashes, infinite loops, normal completion). Your task is to build a program analysis tool that can predict what will happen when these programs run.

Check out the test cases in `cases/jpamb/cases/Simple.java` - these are
(some of) the methods your analyzer will predict the behavior of.

For example, `assertBoolean` has two known outcomes. If given `false` it throws
an `assertion error`, and if given `true` it finishes normally `ok`.

```java
@Case("(false) -> assertion error")
@Case("(true) -> ok")
public static void assertBoolean(boolean shouldFail) {
    assert shouldFail;
}
```

## Getting Started

To get started with this repository, follow the following guides:

- First read and follow the [Setup](docs/setup.md) section.

- Then, consult the [Rules](docs/rules.md) section.

- To get inspired you can take a look at the [Partial Solutions](solutions/). They
  are written in Python so to run them check out the [Python](docs/python.md) section.

- To test a (concrete or abstract) interpreter, take a look at the [Interpret](docs/interpret.md) section.

- To figure out how to extend the benchmark suite consult the [Extending The Benchmark Suite](docs/extending-jpamb.md) section.

## Supported Languages

You can write your analysis in any language you like, however, we have bindings
for Python, which makes it easier to work with the bytecode.

The downside is that running Python applications is a little bit harder.
To effectively do that please consult the [Python](docs/python.md) section.

## Quick Links

- **[uv documentation](https://docs.astral.sh/uv/)** - Python package manager we use
- **[Tree-sitter Java](https://tree-sitter.github.io/tree-sitter/using-parsers)** - For parsing Java source code
- **[JVM2JSON codec](https://github.com/kalhauge/jvm2json/blob/main/CODEC.txt)** - Understanding bytecode format
- **[Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)** - Windows C++ compiler
- **[JPAMB GitHub Issues](https://github.com/kalhauge/jpamb/issues)** - Get help if stuck
