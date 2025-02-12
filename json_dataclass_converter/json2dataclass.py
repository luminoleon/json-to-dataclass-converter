from dataclasses import dataclass
from enum import Enum, auto
import json
import re


class LetterCase(Enum):
    CAMEL = auto()
    SNAKE = auto()
    PASCAL = auto()


class Variable:
    def __init__(self, name, type_hint=None):
        self._name = Variable.sanitize_value_name(name)
        self._type_hint = type_hint
        self._letter_case = Variable._get_letter_case(self._name)

    @staticmethod
    def _get_letter_case(name):
        if re.match(r"^[a-z]+(?:[A-Z0-9_-][a-z0-9_-]+)*$", name):
            return LetterCase.CAMEL
        elif re.match(r"^[a-z0-9]+(?:_[a-z0-9]+)*$", name):
            return LetterCase.SNAKE
        elif re.match(r"^[A-Z][a-z0-9_-]+(?:[A-Z0-9_-][a-z0-9_-]+)*$", name):
            return LetterCase.PASCAL
        else:
            raise ValueError("Invalid variable name")

    @property
    def letter_case(self):
        if self._letter_case is not None:
            return self._letter_case

    @letter_case.setter
    def letter_case(self, value):
        if value not in LetterCase:
            raise ValueError("Invalid letter case")
        if self.letter_case == LetterCase.SNAKE:
            if value == LetterCase.CAMEL:
                self._name = re.sub(
                    r"_(.)", lambda x: x.group(1).upper(), self._name
                )
            elif value == LetterCase.PASCAL:
                self._name = re.sub(
                    r"(?:^|_)(.)", lambda x: x.group(1).upper(), self._name
                )
        elif self.letter_case == LetterCase.CAMEL:
            if value == LetterCase.SNAKE:
                self._name = re.sub(
                    r"([a-z0-9])([A-Z])", r"\1_\2", self._name
                ).lower()
            elif value == LetterCase.PASCAL:
                self._name = self._name[0].upper() + self._name[1:]
        elif self.letter_case == LetterCase.PASCAL:
            if value == LetterCase.SNAKE:
                self._name = re.sub(
                    r"(?<!^)([A-Z])", r"_\1", self._name
                ).lower()
            elif value == LetterCase.CAMEL:
                self._name = self._name[0].lower() + self._name[1:]
        self._letter_case = value

    @property
    def name(self):
        return self._name

    @property
    def type_hint(self):
        return self._type_hint

    @staticmethod
    def sanitize_value_name(name):
        return re.sub(r"\W|^(?=\d)", "_", name)

    def pascal_name(self):
        self.letter_case = LetterCase.PASCAL
        return self.name

    def snake_name(self):
        self.letter_case = LetterCase.SNAKE
        return self.name

    def camel_name(self):
        self.letter_case = LetterCase.CAMEL
        return self.name

    def __repr__(self):
        return f"Variable(name={self.name}, type_hint={self.type_hint}, letter_case={self.letter_case})"


class DataClassGenerator:
    @dataclass
    class Value:
        name: str
        type_hint: str

    def __init__(self, name="JsonClass", use_dataclass_json=False):
        self.name = Variable.sanitize_value_name(name)
        self._inner_classes = []
        self._values = []
        self._use_dataclass_json = use_dataclass_json
        self._typings = []

    def __repr__(self):
        inner_classes_str = [
            inner_class.__repr__() for inner_class in self._inner_classes
        ]
        return (
            f"DataclassBuilder(name={self.name}, inner_classes=["
            f"{', '.join(inner_classes_str)}], values={self._values})"
        )

    @property
    def typings(self):
        return self._typings

    @typings.setter
    def typings(self, value):
        self._typings = value

    @staticmethod
    def get_type_hint(key, value):
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif isinstance(value, list):
            types = []
            for v in value:
                type_hint = DataClassGenerator.get_type_hint(key, v)
                if type_hint not in types:
                    types.append(type_hint)
            return f"List[{' | '.join(types)}]"
        elif isinstance(value, dict):
            return Variable(key).pascal_name()
        else:
            return "Any"

    def add_inner_class(self, inner_class: "DataClassGenerator") -> None:
        if self._inner_classes:
            if inner_class.name in [i.name for i in self._inner_classes]:
                del self._inner_classes[
                    [i.name for i in self._inner_classes].index(
                        inner_class.name
                    )
                ]
        self._inner_classes.append(inner_class)

    def add_variable(self, name, type_hint) -> None:
        if self._values:
            if name in [v.name for v in self._values]:
                del self._values[[v.name for v in self._values].index(name)]
        self._values.append(Variable(name, type_hint))
        if "[" in type_hint:
            self._typings.append(type_hint.split("[")[0])

    def from_dict(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                class_var = Variable(key)
                self.add_inner_class(
                    DataClassGenerator(
                        class_var.pascal_name(), self._use_dataclass_json
                    ).from_dict(value)
                )
                self.add_variable(
                    class_var.snake_name(), class_var.pascal_name()
                )
            else:
                attr_var = Variable(key)
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict):
                            self.add_inner_class(
                                DataClassGenerator(
                                    attr_var.pascal_name(),
                                    self._use_dataclass_json,
                                ).from_dict(v)
                            )
                self.add_variable(
                    attr_var.snake_name(),
                    DataClassGenerator.get_type_hint(key, value),
                )
        return self

    def from_json(self, json_str):
        return self.from_dict(json.loads(json_str))

    def to_string(self, level=0, with_imports=False):
        indent_str = " " * 4 * level
        typings = self.typings
        class_def_str = (
            f"\n{indent_str}@dataclass\n{indent_str}class {self.name}:"
        )
        if self._use_dataclass_json:
            class_def_str = (
                f"\n{indent_str}@dataclass_json(letter_case=LetterCase.CAMEL)"
                + class_def_str
            )
        inner_class_strs = [
            inner_class.to_string(level + 1)
            for inner_class in self._inner_classes
        ]
        [
            typings.extend(inner_class.typings)
            for inner_class in self._inner_classes
        ]

        value_strs = [
            f"{indent_str}    {v.name}: {v.type_hint}" for v in self._values
        ]

        result_str = (
            "\n".join([class_def_str] + inner_class_strs + value_strs) + "\n"
        )
        if level == 0:
            result_str = re.sub(r"\n{3,}", "\n\n", result_str)
            if with_imports:
                if typings:
                    with_imports_str = (
                        "from dataclasses import dataclass\n"
                        f"from typing import {', '.join(typings)}\n\n"
                        "from dataclasses_json import dataclass_json, LetterCase\n\n"
                    )
                else:
                    with_imports_str = (
                        "from dataclasses import dataclass\n\n"
                        "from dataclasses_json import dataclass_json, LetterCase\n\n"
                    )
                return with_imports_str + result_str
            else:
                return result_str.lstrip("\n")
        return result_str
