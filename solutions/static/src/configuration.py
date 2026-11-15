"""Select domains without changing JPAMB's positional argument protocol."""

import argparse
from dataclasses import dataclass

from abstractions import BooleanSet, IntegerAbstraction, SignSet


@dataclass(frozen=True)
class AnalysisConfig:
    """Select integer analysis independently from string support."""

    integer_domain: type[IntegerAbstraction] | None = SignSet
    strings: bool = False

    @property
    def tags(self):
        return [
            "static",
            *(["sign"] if self.integer_domain is not None else []),
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
                "Integer analysis requires --abstractions sign,string"
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
        metavar="sign[,string]",
        help="comma-separated domains: sign, string, or sign,string (default: sign)",
    )
    options, remaining = parser.parse_known_args(arguments)
    names = {name.strip() for name in options.abstractions.split(",")}
    unsupported = names - {"sign", "string"}
    if unsupported:
        parser.error(
            "unsupported abstractions: "
            + ", ".join(sorted(unsupported))
            + ". Available: sign, string. Interval is not implemented yet."
        )
    for argument in remaining:
        if argument.startswith("--"):
            parser.error(f"unrecognized option: {argument}")
    return AnalysisConfig(
        integer_domain=SignSet if "sign" in names else None, strings="string" in names
    ), remaining
