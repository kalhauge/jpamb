# Extending the Benchmark Suite

To get started with adding your own cases, please make sure to download
either `docker` or `podman` (recommended).

You can add your own cases to the benchmark suite by adding
them in the source folder:

```
src/main/java/jpamb/cases
    ├── Arrays.java
    ├── Calls.java
    ├── Loops.java
    ├── Simple.java
    ├── Tricky.java
    └── <YOUR_FILE_HERE>.java
```

Add it to the top of `src/main/java/jpamb/Runtime.java`:

```
public class Runtime {
  static List<Class<?>> caseclasses = List.of(
      Simple.class,
      Loops.class,
      Tricky.class,
      jpamb.cases.Arrays.class,
      Dependent.class, 
      Calls.class, 
      // >> INSERT CLASS HERE
);
```

You then have to update the `caseclasses` list in `src/main/java/jpamb/Runtime.java`, if
you have added a new class and then run:

```
$ uv run jpamb build
```

This will download a docker container and run the build in that. This ensures
consistent builds across systems.

**Warning:** If you create new folders and use docker, it might create them as root. To fix
this either use podman or change the permissions after.

## Cases that use a database

Cases can use JDBC through the fixtures in `jpamb.utils.Db`, which open a fresh
in-memory [H2](https://h2database.com) database per call. They should only use
the `java.sql` interfaces, so `javac` needs no extra classpath.

The cases run with H2 on the classpath. `uv run jpamb build` downloads
`h2-2.5.252.jar` from Maven Central into `lib/` (git-ignored) the first time,
checks its SHA-256, and refuses a jar that does not match. To run a case by
hand:

```
$ java -cp target/classes:lib/h2-2.5.252.jar -ea jpamb.Runtime '<case>' '<input>'
```

Without the jar, the fixtures throw an `IllegalStateException`, so a missing
driver never passes for a `sql error`.

## Updating the `benchmark.sexp` file

Finally, when everything looks good you should update the benchmark file, which contains
information about which instructions are covered by what.

To update this you need to run the following command with an interpreter:

```
$ uv run jpamb build --benchmark <your_interpreter>
```

Please inspect the `target/stats/benchmark.sexp` file and ensure that only the
newly added cases has changed.
