from jpamb import jvm
import jpamb


def test_sourcefile():
    mid = jvm.AbsMethodID.decode("jpamb.cases.Simple.divideByZero:()I")
    assert jpamb.sourcefile(mid).absolute(), "should be absolute"
    assert jpamb.sourcefile(mid).name == "Simple.java", "should be Simple.java"
    assert jpamb.sourcefile(mid).exists(), "should exist"


def test_classfile():
    mid = jvm.AbsMethodID.decode("jpamb.cases.Simple.divideByZero:()I")
    assert jpamb.classfile(mid).absolute(), "should be absolute"
    assert jpamb.classfile(mid).name == "Simple.class", "should be Simple.class"
    assert jpamb.classfile(mid).exists(), "should exist"
