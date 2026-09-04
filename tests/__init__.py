from hypothesis import settings, Verbosity

settings.register_profile("long", max_examples=1000)
settings.register_profile(
    "fast", max_examples=20, phases=["reuse", "generate", "target", "shrink"]
)

settings.load_profile("fast")
