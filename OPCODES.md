#Bytecode instructions
| Mnemonic | Opcode Name |  Exists in |  Count |
| :---- | :---- | :----- | -----: |
| [iload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload_n) | [Load](utils/jvm/opcode.py?plain=1#L735) |  Arrays Dependent IntervalCoverage Loops Simple Tricky | 321 |
| [iconst_i](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iconst_i) | [Push](utils/jvm/opcode.py?plain=1#L102) |  Arrays Dependent Loops Simple Tricky | 319 |
| [dup](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.dup) | [Dup](utils/jvm/opcode.py?plain=1#L258) |  Arrays IntervalCoverage Loops Simple Strings Tricky | 188 |
| [if_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_cond) | [Ifz](utils/jvm/opcode.py?plain=1#L903) |  Arrays Dependent IntervalCoverage Loops Simple Strings Tricky | 171 |
| [ldc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ldc) | [Push](utils/jvm/opcode.py?plain=1#L102) |  Arrays IntervalCoverage Strings | 159 |
| [if_icmp_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_icmp_cond) | [If](utils/jvm/opcode.py?plain=1#L774) |  Arrays IntervalCoverage Tricky | 142 |
| [return](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.return) | [Return](utils/jvm/opcode.py?plain=1#L1125) |  Arrays Calls IntervalCoverage Loops Strings Tricky | 119 |
| [iastore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iastore) | [ArrayStore](utils/jvm/opcode.py?plain=1#L293) |  Arrays | 104 |
| [aload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aload_n) | [Load](utils/jvm/opcode.py?plain=1#L735) |  Arrays Strings | 100 |
| [istore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore_n) | [Store](utils/jvm/opcode.py?plain=1#L585) |  Arrays Loops Tricky | 99 |
| [getstatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.getstatic) | [Get](utils/jvm/opcode.py?plain=1#L841) |  Arrays IntervalCoverage Loops Simple Strings Tricky | 97 |
| [new](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.new) | [New](utils/jvm/opcode.py?plain=1#L973) |  Arrays IntervalCoverage Loops Simple Strings Tricky | 97 |
| [invokespecial](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokespecial) | [InvokeSpecial](utils/jvm/opcode.py?plain=1#L535) |  Arrays IntervalCoverage Loops Simple Strings Tricky | 97 |
| [athrow](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.athrow) | [Throw](utils/jvm/opcode.py?plain=1#L1015) |  Arrays IntervalCoverage Loops Simple Strings Tricky | 97 |
| [goto](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto) | [Goto](utils/jvm/opcode.py?plain=1#L1085) |  Arrays Loops Tricky | 56 |
| [ireturn](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ireturn) | [Return](utils/jvm/opcode.py?plain=1#L1125) |  Dependent Simple | 47 |
| [iinc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iinc) | [Incr](utils/jvm/opcode.py?plain=1#L1052) |  | 45 |
| [idiv](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.idiv) | [Binary](utils/jvm/opcode.py?plain=1#L698) |  Arrays Dependent Simple Tricky | 45 |
| [astore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.astore_n) | [Store](utils/jvm/opcode.py?plain=1#L585) |  Arrays | 38 |
| [arraylength](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.arraylength) | [ArrayLength](utils/jvm/opcode.py?plain=1#L393) |  Arrays | 36 |
| [iaload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iaload) | [ArrayLoad](utils/jvm/opcode.py?plain=1#L359) |  Arrays | 28 |
| [newarray](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.newarray) | [NewArray](utils/jvm/opcode.py?plain=1#L224) |  Arrays | 27 |
| [caload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.caload) | [ArrayLoad](utils/jvm/opcode.py?plain=1#L359) |  | 20 |
| [iadd](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iadd) | [Binary](utils/jvm/opcode.py?plain=1#L698) |  Arrays Loops Tricky | 19 |
| [isub](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.isub) | [Binary](utils/jvm/opcode.py?plain=1#L698) |  Arrays | 17 |
| [iload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload) | [Load](utils/jvm/opcode.py?plain=1#L735) |  Arrays | 16 |
| [invokestatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokestatic) | [InvokeStatic](utils/jvm/opcode.py?plain=1#L462) |  Calls | 16 |
| [imul](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.imul) | [Binary](utils/jvm/opcode.py?plain=1#L698) |  Tricky | 12 |
| [ineg](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ineg) | [Negate](utils/jvm/opcode.py?plain=1#L194) |  | 10 |
| [aconst_null](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aconst_null) | [Push](utils/jvm/opcode.py?plain=1#L102) |  | 7 |
| [istore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore) | [Store](utils/jvm/opcode.py?plain=1#L585) |  Arrays | 7 |
| [invokevirtual](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokevirtual) | [InvokeVirtual](utils/jvm/opcode.py?plain=1#L427) |  Strings | 3 |
| [irem](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.irem) | [Binary](utils/jvm/opcode.py?plain=1#L698) |  Tricky | 3 |
| [i2s](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.i2s) | [Cast](utils/jvm/opcode.py?plain=1#L325) |  Loops | 2 |
