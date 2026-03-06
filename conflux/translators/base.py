# conflux/translators/base.py

from dataclasses import dataclass
from typing import Protocol, Any, List


class Translator(Protocol):
    """
    Interface for all Conflux translators.

    Each translator connects:
        src-language  →  dst-language

    Required structure:
        - name   (string)
        - src    (string)
        - dst    (string)
        - translate(ir, options=None) → IR object
        - check_support(ir) → SimpleReport
    """
    name: str
    src: str
    dst: str

    def translate(self, ir: Any, *, options=None) -> Any:
        ...

    def check_support(self, ir: Any):
        ...


@dataclass
class SimpleReport:
    """
    A lightweight result object to signal whether the input IR
    is supported by a translator.

    ok=True means translation may proceed.
    warnings=[] contains non-fatal issues.
    errors=[] contains fatal issues.
    """
    ok: bool = True
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_error(self, msg: str):
        self.ok = False
        self.errors.append(msg)