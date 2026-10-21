# Proposal: Expanding the JPAMB Suite

We propose expanding the JPAMB suite with new test cases that demonstrate Java runtime vulnerabilities, specifically focusing on unsafe reflection (CWE-470) and insecure deserialization (CWE-502), which can lead to Remote Code Execution (RCE).

## Problem Simplification & Methodology

The objective of these test cases is to trigger an assertion error by successfully routing tainted user input to a vulnerable sink.

While these are simulated scenarios, they reflect the behavior of known sinks commonly found in real-world Java applications. Examples of sinks identified through third-party library analysis (see Sources) include:

* **Arbitrary File Reading (MySQL):** `com.mysql.cj.jdbc.admin.MiniAdmin` (via JDBC URL)
* **XXE / SSRF (MyBatis):** `org.apache.ibatis.parsing.XPathParser` (via XML payload)
* **Insecure Deserialization (JasperReports):** `net.sf.jasperreports.export.SimpleExporterInput` (via serialized file/stream)
* **SSRF (iText / iTextPDF):** `com.itextpdf.text.pdf.codec.GifImage`, `com.itextpdf.text.pdf.RandomAccessFileOrArray`, `com.itextpdf.text.ImgWMF`, `com.lowagie.text.pdf.codec.GifImage` (via URL)
* **Command Injection (JLine):** `jline.internal.TerminalLineSettings`, `jline.UnixTerminal` (via OS command)
* **File Content Leak (dnsjava):** `org.xbill.DNS.tools.jnamed` (via error on file path)
* **Webroot Path Leak (Hutool):** `cn.hutool.core.io.file.FileReader` (via error on invalid file path)

The file also includes gadget chains of length up to 3. They show how simple input checks can be bypassed by constructing a chain of classes that eventually leads to the execution of the vulnerable sink. The key observation is that in real-world scenarios gadget chains are longer and more complex, which sometimes makes it infeasible to construct a call graph that reaches a sink and can be exploited.

## Suite Overview

All methods take attacker-controlled strings. Each `@Case` states the expected outcome (`ok` or `assertion error`).

| Method | CWE | Defense | Ground truth |
|---|---|---|---|
| `unsafe_dispatcher` | 470 | none | vulnerable |
| `weak_dispatcher` | 470 | `startsWith("Safe")`, bypassed by `SafeWrapper`, a subclass of the canary class | vulnerable |
| `strict_safe_dispatcher` | 470 | exact `equals` allowlist | safe |
| `insecure_deserialization` | 502 | none (the object is built before the cast) | vulnerable |
| `blacklist_deserialization` | 502 | blacklist of class names, bypassed by the chain `UpdatedLibrary` → `NotMaintainedDependency` → `__CANARY__Command` | vulnerable |
| `whitelist_deserialization` | 502 | whitelist on the class name only; `DownGradableLibrary` is allowed, and its `legacy` flag activates the gadget | vulnerable |

## Sink Model

The sink is the single method `Vulnerable.canary()`, which throws an `AssertionError`. It is reached from the constructor of `__CANARY__Command`:

* Instantiating the class (directly, through reflection, through a subclass via the implicit `super()`, or through a gadget chain) reaches the sink.
* There is no static initializer. Class initialization is **not** modeled: `Class.forName` alone never triggers the sink, only the instantiation does. This keeps the suite independent of execution order (no `NoClassDefFoundError` on a second run in the same JVM) and avoids the need to support `<clinit>` in an interpreter.

## Mock Deserialization and Simplifications

Real deserialization works on byte streams (`ObjectInputStream.readObject`, `resolveClass`). To keep the suite small and runnable in an interpreter, it is replaced by two simulated methods that take a **string** representing the serialized object:

* `simulateResolveClassName(String payload)` returns the class name encoded in the payload.
* `simulateReadObject(String payload)` returns an instance of the encoded class.

**Payload format:** `serialized_<ClassName>[_legacy]`

| Payload | Resolved class name | Object built |
|---|---|---|
| `serialized_DummyButton` | `DummyButton` | `new DummyButton()` |
| `serialized_SafeCommand` | `SafeCommand` | `new SafeCommand()` |
| `serialized___CANARY__Command` | `__CANARY__Command` | `new __CANARY__Command()` (sink) |
| `serialized_UpdatedLibrary` | `UpdatedLibrary` | `new UpdatedLibrary()` (chain to the sink) |
| `serialized_DownGradableLibrary` | `DownGradableLibrary` | `new DownGradableLibrary(0)` |
| `serialized_DownGradableLibrary_legacy` | `DownGradableLibrary` | `new DownGradableLibrary(1)` (chain to the sink) |

The suffix `_legacy` is stripped by `simulateResolveClassName`, so class-name checks never see it. An unknown name throws `ClassNotFoundException`, and a malformed payload throws `IllegalArgumentException`; both are caught and give `ok`.

The Java bodies are real, so the JVM gives the ground truth for every `@Case`.

### Considerations for the interpreter

The mocks are written so they can be bypassed in a bytecode interpreter that has no `ObjectInputStream`:

1. **Intercept the two methods.** When the interpreter meets `invokestatic` on `jpamb/cases/Vulnerable.simulateResolveClassName` or `simulateReadObject` (descriptors taking and returning `String`/`Object`), it must not execute their bytecode. It decodes the payload itself with the same grammar as above.
2. **Run constructors from the bytecode.** `simulateReadObject` only decides which class to instantiate and with which `legacy` argument. The constructors (`UpdatedLibrary`, `NotMaintainedDependency`, `DownGradableLibrary`, `__CANARY__Command`) are executed normally, so the gadget chains and the final `canary()` call are followed in the real bytecode.
3. **Taint through the mock.** For taint analysis the mocks behave as summaries: the payload parameter flows to the return value (`simulateResolveClassName` returns a string derived from it, `simulateReadObject` returns an object whose class and constructor argument depend on it).
4. **Call graph.** `simulateReadObject` has statically known targets (the constructors listed above). The class chosen depends on the input, so a precise call graph needs the summary and not the decoder's string operations.

What the simplification does **not** model:

* Byte streams, object graphs, `readObject`/`readResolve` hooks, and `ObjectInputFilter`.
* Field values other than the `legacy` flag.
* Real class loading by name during deserialization; the mapping from name to class is fixed.

These are deliberate. They keep the exploitable logic (a validation of the class name that does not cover the behavior of the allowed or unlisted classes) and remove the serialization format.

### Reflection

For `CWE-470` the dispatchers use the real API: `Class.forName("jpamb.cases.Vulnerable$" + ctl + "Command")` followed by `Class.newInstance()`, then a cast to `SafeCommand`. The interpreter must support loading the nested classes of `jpamb.cases.Vulnerable` by name and instantiating them with `newInstance()`. `Class.newInstance()` is used on purpose: it propagates errors thrown by the constructor, while `getDeclaredConstructor().newInstance()` would wrap them in an `InvocationTargetException` and the surrounding `catch (Exception)` would hide the assertion error.

## Sources and Inspiration

1. **CWE-470:** [Use of Externally-Controlled Input to Select Classes or Code ('Unsafe Reflection')](https://cwe.mitre.org/data/definitions/470.html)
2. **CWE-502:** [Deserialization of Untrusted Data](https://cwe.mitre.org/data/definitions/502.html)
3. **Conviso AppSec Blog:** [Finding classes to exploit insecure/unchecked vulnerabilities in Java with Joern](https://blog.convisoappsec.com/finding-classes-to-exploit-insecure-unchecked-vulnerabilities-in-java-with-joern/)