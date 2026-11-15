"""Select domains without changing JPAMB's positional argument protocol."""

import argparse
from dataclasses import dataclass

from abstractions import BooleanSet, IntegerAbstraction, Interval, SignInterval, SignSet


@dataclass(frozen=True)
class AnalysisConfig:
    """Select integer analysis independently from string support."""

    integer_domain: type[IntegerAbstraction] | None = SignSet
    strings: bool = False

    @property
    def tags(self):
        return [
            "static",
            *(["sign"] if self.integer_domain in (SignSet, SignInterval) else []),
            *(["interval"] if self.integer_domain in (Interval, SignInterval) else []),
            *(["string"] if self.strings else []),
            "python",
        ]

    def scalar(self, values):
        """Construct integers when enabled, otherwise only JVM boolean values."""
        domain = self.integer_domain if self.integer_domain is not None else BooleanSet
        return domain.abstract(values)

    def require_integers(self):
        if self.integer_domain is None:
            raise NotImplementedError(
                "Integer analysis requires sign or interval in --abstractions"
            )
        return self.integer_domain


DEFAULT_CONFIG = AnalysisConfig()


def parse_options(arguments):
    """Return configuration and the remaining JPAMB arguments (including info)."""
    parser = argparse.ArgumentParser(
        description="JPAMB static analyzer. String-only mode uses minimal booleans, not signs.",
        epilog="Example: jpamb analyse -- static-analysis --abstractions sign,string",
    )
    parser.add_argument(
        "--abstractions",
        default="sign",
        metavar="DOMAIN[,DOMAIN...]",
        help="comma-separated domains: sign, interval, string; any combination (default: sign)",
    )
    options, remaining = parser.parse_known_args(arguments)
    names = {name.strip() for name in options.abstractions.split(",")}
    unsupported = names - {"sign", "interval", "string"}
    if unsupported:
        parser.error(
            "unsupported abstractions: "
            + ", ".join(sorted(unsupported))
            + ". Available: sign, interval, string."
        )
    for argument in remaining:
        if argument.startswith("--"):
            parser.error(f"unrecognized option: {argument}")
    if "sign" in names and "interval" in names:
        integer_domain = SignInterval
    elif "interval" in names:
        integer_domain = Interval
    elif "sign" in names:
        integer_domain = SignSet
    else:
        integer_domain = None
    return AnalysisConfig(
        integer_domain=integer_domain, strings="string" in names
    ), remaining
