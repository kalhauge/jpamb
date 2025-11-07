#Bytecode instructions
| Mnemonic | Opcode Name |  Exists in |  Count |
| :---- | :---- | :----- | -----: |
 | [iconst_i](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iconst_i) | [Push](jpamb/jvm/opcode.py?plain=1#L116) |  Simple Loops Tricky Arrays Calls | 120 |
 | [iload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload_n) | [Load](jpamb/jvm/opcode.py?plain=1#L651) |  Simple Loops Tricky Arrays Calls | 92 |
 | [if_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_cond) | [Ifz](jpamb/jvm/opcode.py?plain=1#L816) |  Loops Tricky Arrays Calls | 66 |
 | [dup](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.dup) | [Dup](jpamb/jvm/opcode.py?plain=1#L219) |  Loops Tricky Arrays Calls | 59 |
 | [return](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.return) | [Return](jpamb/jvm/opcode.py?plain=1#L1042) |  Loops Tricky Arrays Calls | 45 |
 | [aload_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aload_n) | [Load](jpamb/jvm/opcode.py?plain=1#L651) |  Arrays Calls | 41 |
 | [ldc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ldc) | [Push](jpamb/jvm/opcode.py?plain=1#L116) |  Simple Arrays | 38 |
 | [if_icmp_cond](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_icmp_cond) | [If](jpamb/jvm/opcode.py?plain=1#L690) |  Tricky Arrays Calls | 38 |
 | [getstatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.getstatic) | [Get](jpamb/jvm/opcode.py?plain=1#L755) |  Loops Tricky Arrays Calls | 36 |
 | [new](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.new) | [New](jpamb/jvm/opcode.py?plain=1#L884) |  Loops Tricky Arrays Calls | 36 |
 | [invokespecial](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokespecial) | [InvokeSpecial](jpamb/jvm/opcode.py?plain=1#L496) |  Loops Tricky Arrays Calls | 36 |
 | [athrow](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.athrow) | [Throw](jpamb/jvm/opcode.py?plain=1#L923) |  Loops Tricky Arrays Calls | 36 |
 | [istore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore_n) | [Store](jpamb/jvm/opcode.py?plain=1#L546) |  Loops Tricky Arrays Calls | 29 |
 | [iastore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iastore) | [ArrayStore](jpamb/jvm/opcode.py?plain=1#L254) |  | 28 |
 | [idiv](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.idiv) | [Binary](jpamb/jvm/opcode.py?plain=1#L614) |  Simple Tricky | 20 |
 | [ireturn](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ireturn) | [Return](jpamb/jvm/opcode.py?plain=1#L1042) |  Simple | 20 |
 | [goto](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto) | [Goto](jpamb/jvm/opcode.py?plain=1#L1002) |  Loops Tricky Arrays Calls | 18 |
 | [astore_n](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.astore_n) | [Store](jpamb/jvm/opcode.py?plain=1#L546) |  Calls | 15 |
 | [caload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.caload) | [ArrayLoad](jpamb/jvm/opcode.py?plain=1#L320) |  | 15 |
 | [arraylength](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.arraylength) | [ArrayLength](jpamb/jvm/opcode.py?plain=1#L354) |  Arrays Calls | 12 |
 | [iload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload) | [Load](jpamb/jvm/opcode.py?plain=1#L651) |  Calls | 11 |
 | [iadd](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iadd) | [Binary](jpamb/jvm/opcode.py?plain=1#L614) |  Loops Tricky Arrays | 10 |
 | [invokestatic](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokestatic) | [InvokeStatic](jpamb/jvm/opcode.py?plain=1#L423) |  Calls | 10 |
 | [iaload](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iaload) | [ArrayLoad](jpamb/jvm/opcode.py?plain=1#L320) |  Arrays Calls | 9 |
 | [isub](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.isub) | [Binary](jpamb/jvm/opcode.py?plain=1#L614) |  Simple | 8 |
 | [newarray](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.newarray) | [NewArray](jpamb/jvm/opcode.py?plain=1#L180) |  | 8 |
 | [iinc](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iinc) | [Incr](jpamb/jvm/opcode.py?plain=1#L960) |  Arrays Calls | 6 |
 | [istore](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore) | [Store](jpamb/jvm/opcode.py?plain=1#L546) |  Calls | 5 |
 | [aconst_null](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aconst_null) | [Push](jpamb/jvm/opcode.py?plain=1#L116) |  | 4 |
 | [imul](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.imul) | [Binary](jpamb/jvm/opcode.py?plain=1#L614) |  Tricky | 3 |
 | [irem](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.irem) | [Binary](jpamb/jvm/opcode.py?plain=1#L614) |  Tricky | 2 |
 | [i2s](https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.i2s) | [Cast](jpamb/jvm/opcode.py?plain=1#L286) |  Loops | 1 |
