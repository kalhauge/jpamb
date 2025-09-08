import jpamb
import logging

methodid = jpamb.getmethodid(
    "conservative",
    "0.1",
    "Sejt gruppenavn",
    ["her er tags", "her er flere"],
    for_science=True,
    
)

log = logging
log.basicConfig(level=logging.DEBUG)

log.debug(methodid)
log.debug(methodid.classname)

cf = jpamb.Suite().sourcefile(methodid.classname)

n = open(cf).read()

if "assert" in n:
    print("assertion error;1")
else:
    print("assertion error;10%")

