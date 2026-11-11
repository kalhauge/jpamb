#Bytecode instructions
| Mnemonic | Opcode Name |  Exists in |  Count |
| :---- | :---- | :----- | -----: |
| [iload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload_n) | [Load](src/jvm/opcode.py?plain=1#L735) |  Arrays Calls Dependent Group25 Loops Simple Tricky | 339 |
| [iconst_i](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iconst_i) | [Push](src/jvm/opcode.py?plain=1#L102) |  Arrays Calls Dependent Group25 Loops Simple Tricky | 241 |
| [if_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_cond) | [Ifz](src/jvm/opcode.py?plain=1#L903) |  Arrays Calls Dependent Group25 Loops Simple Strings Tricky | 157 |
| [dup](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.dup) | [Dup](src/jvm/opcode.py?plain=1#L258) |  Arrays Calls Dependent Group25 Loops Simple Strings Tricky | 122 |
| [istore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore_n) | [Store](src/jvm/opcode.py?plain=1#L585) |  Arrays Calls Dependent Group25 Loops Tricky | 88 |
| [aload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aload_n) | [Load](src/jvm/opcode.py?plain=1#L735) |  Arrays Calls Group25 Strings | 88 |
| [ldc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ldc) | [Push](src/jvm/opcode.py?plain=1#L102) |  Arrays Calls Dependent Group25 Simple Strings | 87 |
| [if_icmp_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_icmp_cond) | [If](src/jvm/opcode.py?plain=1#L774) |  Arrays Calls Dependent Group25 Simple Tricky | 86 |
| [return](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.return) | [Return](src/jvm/opcode.py?plain=1#L1125) |  Arrays Calls Dependent Loops Simple Strings Tricky | 85 |
| [ireturn](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ireturn) | [Return](src/jvm/opcode.py?plain=1#L1125) |  Dependent Group25 Loops Simple | 77 |
| [getstatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.getstatic) | [Get](src/jvm/opcode.py?plain=1#L841) |  Arrays Calls Dependent Group25 Loops Simple Strings Tricky | 72 |
| [new](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.new) | [New](src/jvm/opcode.py?plain=1#L973) |  Arrays Calls Dependent Group25 Loops Simple Strings Tricky | 72 |
| [invokespecial](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokespecial) | [InvokeSpecial](src/jvm/opcode.py?plain=1#L535) |  Arrays Calls Dependent Group25 Loops Simple Strings Tricky | 72 |
| [athrow](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.athrow) | [Throw](src/jvm/opcode.py?plain=1#L1015) |  Arrays Calls Dependent Group25 Loops Simple Strings Tricky | 72 |
| [iastore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iastore) | [ArrayStore](src/jvm/opcode.py?plain=1#L293) |  Arrays Group25 | 62 |
| [idiv](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.idiv) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Arrays Dependent Group25 Loops Simple Tricky | 49 |
| [invokestatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokestatic) | [InvokeStatic](src/jvm/opcode.py?plain=1#L462) |  Calls Group25 | 38 |
| [goto](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto) | [Goto](src/jvm/opcode.py?plain=1#L1085) |  Arrays Calls Dependent Group25 Loops Tricky | 37 |
| [iload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload) | [Load](src/jvm/opcode.py?plain=1#L735) |  Arrays Calls Group25 | 31 |
| [astore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.astore_n) | [Store](src/jvm/opcode.py?plain=1#L585) |  Arrays Calls Group25 | 30 |
| [arraylength](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.arraylength) | [ArrayLength](src/jvm/opcode.py?plain=1#L393) |  Arrays Calls Group25 | 27 |
| [isub](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.isub) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Arrays Dependent Group25 Simple | 26 |
| [iadd](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iadd) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Arrays Group25 Loops Simple Tricky | 25 |
| [iaload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iaload) | [ArrayLoad](src/jvm/opcode.py?plain=1#L359) |  Arrays Calls Group25 | 23 |
| [iinc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iinc) | [Incr](src/jvm/opcode.py?plain=1#L1052) |  Arrays Calls Dependent Group25 | 21 |
| [caload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.caload) | [ArrayLoad](src/jvm/opcode.py?plain=1#L359) |  Arrays | 20 |
| [newarray](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.newarray) | [NewArray](src/jvm/opcode.py?plain=1#L224) |  Arrays Group25 | 19 |
| [irem](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.irem) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Group25 Tricky | 17 |
| [istore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore) | [Store](src/jvm/opcode.py?plain=1#L585) |  Arrays Calls Group25 | 12 |
| [ineg](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ineg) | [Negate](src/jvm/opcode.py?plain=1#L194) |  Dependent | 10 |
| [aconst_null](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aconst_null) | [Push](src/jvm/opcode.py?plain=1#L102) |  Arrays | 7 |
| [imul](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.imul) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Simple Tricky | 5 |
| [areturn](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.areturn) | [Return](src/jvm/opcode.py?plain=1#L1125) |  Group25 | 3 |
| [invokevirtual](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokevirtual) | [InvokeVirtual](src/jvm/opcode.py?plain=1#L427) |  Strings | 3 |
| [i2s](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.i2s) | [Cast](src/jvm/opcode.py?plain=1#L325) |  Loops | 2 |
