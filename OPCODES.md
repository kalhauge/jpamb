#Bytecode instructions
| Mnemonic | Opcode Name |  Exists in |  Count |
| :---- | :---- | :----- | -----: |
| [iload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload_n) | [Load](utils/jvm/opcode.py?plain=1#L716) |  Arrays Dependent Loops Simple Tricky | 139 |
| [iconst_i](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iconst_i) | [Push](utils/jvm/opcode.py?plain=1#L121) |  Arrays Dependent Loops Simple Tricky | 129 |
| [if_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_cond) | [Ifz](utils/jvm/opcode.py?plain=1#L883) |  Arrays Dependent Loops Simple Strings Tricky | 81 |
| [dup](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.dup) | [Dup](utils/jvm/opcode.py?plain=1#L251) |  Arrays Loops Simple Strings Tricky | 63 |
| [return](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.return) | [Return](utils/jvm/opcode.py?plain=1#L1102) |  Arrays Calls Loops Strings Tricky | 49 |
| [if_icmp_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_icmp_cond) | [If](utils/jvm/opcode.py?plain=1#L755) |  Arrays Tricky | 45 |
| [ldc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ldc) | [Push](utils/jvm/opcode.py?plain=1#L121) |  Arrays Strings | 44 |
| [aload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aload_n) | [Load](utils/jvm/opcode.py?plain=1#L716) |  Arrays Strings | 43 |
| [istore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore_n) | [Store](utils/jvm/opcode.py?plain=1#L578) |  Arrays Loops Tricky | 42 |
| [getstatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.getstatic) | [Get](utils/jvm/opcode.py?plain=1#L822) |  Arrays Loops Simple Strings Tricky | 40 |
| [new](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.new) | [New](utils/jvm/opcode.py?plain=1#L953) |  Arrays Loops Simple Strings Tricky | 40 |
| [invokespecial](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokespecial) | [InvokeSpecial](utils/jvm/opcode.py?plain=1#L528) |  Arrays Loops Simple Strings Tricky | 40 |
| [athrow](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.athrow) | [Throw](utils/jvm/opcode.py?plain=1#L992) |  Arrays Loops Simple Strings Tricky | 40 |
| [ireturn](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ireturn) | [Return](utils/jvm/opcode.py?plain=1#L1102) |  Dependent Simple | 31 |
| [idiv](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.idiv) | [Binary](utils/jvm/opcode.py?plain=1#L679) |  Arrays Dependent Simple Tricky | 30 |
| [iastore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iastore) | [ArrayStore](utils/jvm/opcode.py?plain=1#L286) |  Arrays | 28 |
| [goto](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto) | [Goto](utils/jvm/opcode.py?plain=1#L1062) |  Arrays Loops Tricky | 20 |
| [astore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.astore_n) | [Store](utils/jvm/opcode.py?plain=1#L578) |  Arrays | 15 |
| [caload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.caload) | [ArrayLoad](utils/jvm/opcode.py?plain=1#L352) |  | 15 |
| [arraylength](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.arraylength) | [ArrayLength](utils/jvm/opcode.py?plain=1#L386) |  Arrays | 12 |
| [isub](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.isub) | [Binary](utils/jvm/opcode.py?plain=1#L679) |  Arrays | 11 |
| [iload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload) | [Load](utils/jvm/opcode.py?plain=1#L716) |  Arrays | 11 |
| [iadd](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iadd) | [Binary](utils/jvm/opcode.py?plain=1#L679) |  Arrays Loops Tricky | 10 |
| [invokestatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokestatic) | [InvokeStatic](utils/jvm/opcode.py?plain=1#L455) |  Calls | 10 |
| [iaload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iaload) | [ArrayLoad](utils/jvm/opcode.py?plain=1#L352) |  Arrays | 9 |
| [newarray](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.newarray) | [NewArray](utils/jvm/opcode.py?plain=1#L217) |  Arrays | 8 |
| [iinc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iinc) | [Incr](utils/jvm/opcode.py?plain=1#L1029) |  | 8 |
| [ineg](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ineg) | [Negate](utils/jvm/opcode.py?plain=1#L189) |  | 6 |
| [istore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore) | [Store](utils/jvm/opcode.py?plain=1#L578) |  Arrays | 5 |
| [aconst_null](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aconst_null) | [Push](utils/jvm/opcode.py?plain=1#L121) |  | 4 |
| [imul](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.imul) | [Binary](utils/jvm/opcode.py?plain=1#L679) |  Tricky | 3 |
| [invokevirtual](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokevirtual) | [InvokeVirtual](utils/jvm/opcode.py?plain=1#L420) |  Strings | 2 |
| [irem](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.irem) | [Binary](utils/jvm/opcode.py?plain=1#L679) |  Tricky | 2 |
| [i2s](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.i2s) | [Cast](utils/jvm/opcode.py?plain=1#L318) |  Loops | 1 |
