#Bytecode instructions
| Mnemonic | Opcode Name |  Exists in |  Count |
| :---- | :---- | :----- | -----: |
| [iload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload_n) | [Load](src/jvm/opcode.py?plain=1#L735) |  Arrays Calls Dependent Loops MagicConstants Simple Tricky | 253 |
| [iconst_i](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iconst_i) | [Push](src/jvm/opcode.py?plain=1#L102) |  Arrays Calls Dependent Loops MagicConstants Simple Tricky | 247 |
| [if_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_cond) | [Ifz](src/jvm/opcode.py?plain=1#L903) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 135 |
| [dup](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.dup) | [Dup](src/jvm/opcode.py?plain=1#L258) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 119 |
| [return](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.return) | [Return](src/jvm/opcode.py?plain=1#L1125) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 91 |
| [ldc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ldc) | [Push](src/jvm/opcode.py?plain=1#L102) |  Arrays Calls Dependent MagicConstants Simple Strings | 90 |
| [if_icmp_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_icmp_cond) | [If](src/jvm/opcode.py?plain=1#L774) |  Arrays Calls Dependent MagicConstants Simple Tricky | 81 |
| [istore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore_n) | [Store](src/jvm/opcode.py?plain=1#L585) |  Arrays Calls Dependent Loops MagicConstants Tricky | 77 |
| [aload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aload_n) | [Load](src/jvm/opcode.py?plain=1#L735) |  Arrays Calls MagicConstants Strings | 76 |
| [getstatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.getstatic) | [Get](src/jvm/opcode.py?plain=1#L841) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 69 |
| [new](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.new) | [New](src/jvm/opcode.py?plain=1#L973) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 69 |
| [invokespecial](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokespecial) | [InvokeSpecial](src/jvm/opcode.py?plain=1#L535) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 69 |
| [athrow](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.athrow) | [Throw](src/jvm/opcode.py?plain=1#L1015) |  Arrays Calls Dependent Loops MagicConstants Simple Strings Tricky | 69 |
| [iastore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iastore) | [ArrayStore](src/jvm/opcode.py?plain=1#L293) |  Arrays | 59 |
| [ireturn](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ireturn) | [Return](src/jvm/opcode.py?plain=1#L1125) |  Dependent Loops MagicConstants Simple | 59 |
| [idiv](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.idiv) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Arrays Dependent Loops MagicConstants Simple Tricky | 48 |
| [goto](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto) | [Goto](src/jvm/opcode.py?plain=1#L1085) |  Arrays Calls Dependent Loops MagicConstants Tricky | 37 |
| [astore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.astore_n) | [Store](src/jvm/opcode.py?plain=1#L585) |  Arrays Calls MagicConstants | 36 |
| [iaload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iaload) | [ArrayLoad](src/jvm/opcode.py?plain=1#L359) |  Arrays Calls MagicConstants | 23 |
| [isub](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.isub) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Arrays Dependent MagicConstants Simple | 23 |
| [newarray](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.newarray) | [NewArray](src/jvm/opcode.py?plain=1#L224) |  Arrays MagicConstants | 22 |
| [arraylength](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.arraylength) | [ArrayLength](src/jvm/opcode.py?plain=1#L393) |  Arrays Calls | 21 |
| [iinc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iinc) | [Incr](src/jvm/opcode.py?plain=1#L1052) |  Arrays Calls Dependent MagicConstants | 20 |
| [caload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.caload) | [ArrayLoad](src/jvm/opcode.py?plain=1#L359) |  Arrays | 20 |
| [iadd](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iadd) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Arrays Loops MagicConstants Simple Tricky | 19 |
| [iload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload) | [Load](src/jvm/opcode.py?plain=1#L735) |  Arrays Calls | 16 |
| [invokestatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokestatic) | [InvokeStatic](src/jvm/opcode.py?plain=1#L462) |  Calls | 16 |
| [imul](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.imul) | [Binary](src/jvm/opcode.py?plain=1#L698) |  MagicConstants Simple Tricky | 14 |
| [aconst_null](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aconst_null) | [Push](src/jvm/opcode.py?plain=1#L102) |  Arrays MagicConstants | 10 |
| [ineg](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ineg) | [Negate](src/jvm/opcode.py?plain=1#L194) |  Dependent | 10 |
| [istore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore) | [Store](src/jvm/opcode.py?plain=1#L585) |  Arrays Calls | 7 |
| [invokevirtual](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokevirtual) | [InvokeVirtual](src/jvm/opcode.py?plain=1#L427) |  Strings | 3 |
| [irem](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.irem) | [Binary](src/jvm/opcode.py?plain=1#L698) |  Tricky | 3 |
| [i2s](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.i2s) | [Cast](src/jvm/opcode.py?plain=1#L325) |  Loops | 2 |
