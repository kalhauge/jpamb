# Interpret

The second mode in JPAMB, is the interpret mode. I this mode, your interpreter is presented with a method, one of the inputs, and
a maximum number of steps.
The goal of your interpreter is to provide the sequences of steps, not exceeding the maximum.

## Rules

Besides the info argument (see ()[docs/rules.md]), you will be provided with
as list of

You might be presented with the arguments, like so:

```bash
$ <your-interpreter> <methodid> <input> <max_steps>
```

First you emit the initial state as an (S-expression)\[/doc/sexpr.md\]:

```lisp
(init :state <initial-state>)
```

Then you proceed by changing the state step by step.

```lisp
(step :pc "<methodid>:<offset>" 
  :edit <edits-to-the-state>
  :edit ...
  ...
)
```

The edits can be one of `insert`, `update`, `delete`.

## Example

For example, for the following `checkBeforeDivideByN`, example (see below):

```java
@Case("(1) -> ok")
@Case("(0) -> assertion error")
public static int checkBeforeDivideByN(int n) {
    assert n != 0;
    return 1 / n;
}
```

You might be presented with the arguments:

```bash
$ <your-interpreter> 'jpamb.cases.Simple.checkBeforeDivideByN:(I)I' '(0)' 100
```

And you should now produce the steps to get to the assertion error.
First we emit the initial state:

```lisp
(init :state (state
    :heap ()
    :frames (
      :00 (frame
        :locals (
          :00 (int 0)
        )
        :stack ()
        :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:0"
      )
    )
  )
)
```

Then we emit all steps until we reach a final state.

```lisp
(step
  :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:0"
  :edit (insert
    :path (2/frames 0/00 2/stack 0/00)
    :value (int 0)
  )
  :edit (update
    :path (2/frames 0/00 3/pc)
    :a "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:0"
    :b "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:1"
  )
)
(step
  :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:1"
  :edit (delete
    :path (2/frames 0/00 2/stack 0/00)
    :value (int 0)
  )
  :edit (update
    :path (2/frames 0/00 3/pc)
    :a "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:1"
    :b "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:2"
  )
)
(step
  :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:2"
  :edit (insert
    :path (2/frames 0/00 2/stack 0/00)
    :value (int 0)
  )
  :edit (update
    :path (2/frames 0/00 3/pc)
    :a "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:2"
    :b "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:3"
  )
)
(step
  :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:3"
  :edit (delete
    :path (2/frames 0/00 2/stack 0/00)
    :value (int 0)
  )
  :edit (update
    :path (2/frames 0/00 3/pc)
    :a "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:3"
    :b "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:4"
  )
)
(step
  :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:4"
  :edit (update
    :path ()
    :a (state
      :heap ()
      :frames (
        :00 (frame
          :locals (
            :00 (int 0)
          )
          :stack ()
          :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:4"
        )
      )
    )
    :b "assertion error"
  )
)
```
