# Proposal: Expanding the JPAMB Suite

We propose expanding the JPAMB suite with new test cases that demonstrate Java runtime vulnerabilities, specifically focusing on unsafe reflection (CWE-470) and insecure deserialization (CWE-502), which can lead, for instance, to Remote Code Execution (RCE).

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

The file also includes gadget chains of length up to 3. They show how simple input checks can be bypassed by constructing a chain of classes that eventually leads to the execution of the vulnerable sink. The key observation is that in real-world scenarios gadget chains are longer and more complex.

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
* There is no static initializer. Class initialization is **not** modeled: `Class.forName` alone never triggers the sink, only the instantiation does.

## Mock Deserialization and Simplifications

Real deserialization works on byte streams (`ObjectInputStream.readObject`, `resolveClass`). To keep the suite small and runnable in an interpreter, it is replaced by two simulated methods that take a **string** representing the serialized object:

* `simulateResolveClassName(String payload)` validates the payload and returns the class name encoded in it.
* `simulateReadObject(String payload)` returns an instance of the encoded class, built with the encoded parameters.

**Payload format:** `header|classname|params`

The payload is split on `|` into exactly three fields (trailing empty fields are kept, so `SER|DummyButton|` is valid and has an empty `params`):

| Field | Meaning |
|---|---|
| `header` | Must be exactly `SER`. |
| `classname` | Name of the class to instantiate. Must not be empty. |
| `params` | Constructor parameters. Empty for most classes; for `DownGradableLibrary` it is the legacy flag as an integer. |

| Payload | Resolved class name | Object built |
|---|---|---|
| `SER\|DummyButton\|` | `DummyButton` | `new DummyButton()` |
| `SER\|SafeCommand\|` | `SafeCommand` | `new SafeCommand()` |
| `SER\|__CANARY__Command\|` | `__CANARY__Command` | `new __CANARY__Command()` (sink) |
| `SER\|UpdatedLibrary\|` | `UpdatedLibrary` | `new UpdatedLibrary()` (chain to the sink) |
| `SER\|DownGradableLibrary\|0` | `DownGradableLibrary` | `new DownGradableLibrary(0)` |
| `SER\|DownGradableLibrary\|1` | `DownGradableLibrary` | `new DownGradableLibrary(1)` (chain to the sink) |

**Validation and errors**

`simulateResolveClassName` throws `IllegalArgumentException` when:

* the payload does not have exactly 3 fields (`Malformed payload`);
* the header is not `SER` (`Invalid header`);
* the class name is empty.

`simulateReadObject` additionally throws:

* `IllegalArgumentException` if `params` is non-empty for a class that expects none (`DummyButton`, `SafeCommand`, `__CANARY__Command`, `UpdatedLibrary`), if `params` is empty for `DownGradableLibrary`, or if the `DownGradableLibrary` parameter is not a valid integer;
* `ClassNotFoundException` for an unknown class name.

All these exceptions are caught by the test methods and result in `ok`.

The Java bodies are real, so the JVM gives the ground truth for every `@Case`.

## Sources and Inspiration

1. **CWE-470:** [Use of Externally-Controlled Input to Select Classes or Code ('Unsafe Reflection')](https://cwe.mitre.org/data/definitions/470.html)
2. **CWE-502:** [Deserialization of Untrusted Data](https://cwe.mitre.org/data/definitions/502.html)
3. **Conviso AppSec Blog:** [Finding classes to exploit insecure/unchecked vulnerabilities in Java with Joern](https://blog.convisoappsec.com/finding-classes-to-exploit-insecure-unchecked-vulnerabilities-in-java-with-joern/)