import re

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def require_identifier(value: str, field_name: str) -> None:
    if _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(f"invalid {field_name}: {value!r}")


def require_name(value: str, field_name: str = "name") -> None:
    if value.strip() == "":
        raise ValueError(f"invalid {field_name}: {value!r}")
