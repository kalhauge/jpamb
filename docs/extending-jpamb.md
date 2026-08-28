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
