from enum import Enum


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
