from enum import Enum

from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase


class Message(Enum):
    SUCCESS = "Success"
    ERROR = "Error"
    WARNING = "Warning"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Json2DataclassResponse:
    message: Message
    data: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ErrorResponse:
    message: Message
    data: str
