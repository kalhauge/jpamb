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

Then you proceed by listing the states one by one, following the scheme:

```lisp
(step :before <before-state> :pc "<methodid>:<offset>" :after <after-state>)
```

The after-state can either be a new state or final state, in which case it should be a string.

**Note**, The before state must match the previous state.

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
    :before (state
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
    :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:0"
    :after (state
      :heap ()
      :frames (
        :00 (frame
          :locals (
            :00 (int 0)
          )
          :stack (
            :00 (int 0)
          )
          :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:1"
        )
      )
    )
  ) 
... many steps later ...
(step
    :before (state
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
    :pc "jpamb.cases.Simple.checkBeforeDivideByN:(I)I:4"
    :after "assertion error"
  )
```
