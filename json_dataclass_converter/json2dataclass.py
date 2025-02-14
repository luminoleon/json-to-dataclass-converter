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
        self._name = Variable.sanitize_name(name)
        self._type_hint = type_hint
        self._letter_case = Variable._get_letter_case(self._name)
        self._pascal_name = Variable._convert_letter_case(
            self._name, self._letter_case, LetterCase.PASCAL
        )
        self._camel_name = Variable._convert_letter_case(
            self._name, self._letter_case, LetterCase.CAMEL
        )
        self._snake_name = Variable._convert_letter_case(
            self._name, self._letter_case, LetterCase.SNAKE
        )

    @staticmethod
    def _get_letter_case(name):
        name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
        name = re.sub(r"^[^a-zA-Z]*", "", name)
        if re.match(r"^[a-z]+(?:[A-Z0-9_-]*[a-z0-9_-]*)*$", name):
            return LetterCase.CAMEL
        elif re.match(r"^[a-z]+(?:_[a-z0-9]+)*$", name):
            return LetterCase.SNAKE
        elif re.match(r"^[A-Z]+(?:[A-Z0-9_-]*[a-z0-9_-]*)*$", name):
            return LetterCase.PASCAL
        else:
            print(name)
            raise ValueError("Invalid variable name")

    @property
    def letter_case(self):
        if self._letter_case is not None:
            return self._letter_case

    @letter_case.setter
    def letter_case(self, value):
        if value not in LetterCase:
            raise ValueError("Invalid letter case")
        self._letter_case = value

    @staticmethod
    def _convert_letter_case(name, src_letter_case, dest_letter_case):
        if dest_letter_case not in LetterCase:
            raise ValueError("Invalid letter case")
        if src_letter_case == LetterCase.SNAKE:
            if dest_letter_case == LetterCase.CAMEL:
                name = re.sub(r"_(.)", lambda x: x.group(1).upper(), name)
            elif dest_letter_case == LetterCase.PASCAL:
                name = re.sub(
                    r"(?:^|_)(.)", lambda x: x.group(1).upper(), name
                )
        elif src_letter_case == LetterCase.CAMEL:
            if dest_letter_case == LetterCase.SNAKE:
                name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()
            elif dest_letter_case == LetterCase.PASCAL:
                name = name[0].upper() + name[1:]
        elif src_letter_case == LetterCase.PASCAL:
            if dest_letter_case == LetterCase.SNAKE:
                name = re.sub(r"(?<!^)(?<![A-Z])([A-Z])", r"_\1", name)
                name = re.sub(
                    r"(?<!^)(?<!_)([A-Z])(?![A-Z])", r"_\1", name
                ).lower()
            elif dest_letter_case == LetterCase.CAMEL:
                name = name[0].lower() + name[1:]
        return name

    @property
    def name(self):
        return self._name

    @property
    def type_hint(self):
        return self._type_hint

    @staticmethod
    def sanitize_name(name):
        return re.sub(r"\W|^(?=\d)", "_", name)

    @property
    def pascal_name(self):
        return self._pascal_name

    @property
    def snake_name(self):
        return self._snake_name

    @property
    def camel_name(self):
        return self._camel_name

    def __repr__(self):
        return f"Variable(name={self.name!r}, type_hint={self.type_hint!r}, letter_case={self.letter_case})"


class DataClassGenerator:
    typings = set()

    def __init__(self, name="JsonClass", use_dataclass_json=False):
        self.name = Variable.sanitize_name(name)
        self._inner_classes = []
        self._variables = []
        self._use_dataclass_json = use_dataclass_json

    def __repr__(self):
        inner_classes_str = [
            inner_class.__repr__() for inner_class in self._inner_classes
        ]
        return (
            f"DataclassBuilder(name={self.name}, inner_classes=["
            f"{', '.join(inner_classes_str)}], values={self._variables})"
        )

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
            return Variable(key).pascal_name
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
        if self._variables:
            if name in [v.name for v in self._variables]:
                del self._variables[
                    [v.name for v in self._variables].index(name)
                ]
        self._variables.append(Variable(name, type_hint))
        if "[" in type_hint:
            self.typings.add(type_hint.split("[")[0])

    def from_dict(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                class_var = Variable(key)
                self.add_inner_class(
                    DataClassGenerator(
                        class_var.pascal_name, self._use_dataclass_json
                    ).from_dict(value)
                )
                self.add_variable(class_var.snake_name, class_var.pascal_name)
            else:
                attr_var = Variable(key)
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict):
                            self.add_inner_class(
                                DataClassGenerator(
                                    attr_var.pascal_name,
                                    self._use_dataclass_json,
                                ).from_dict(v)
                            )
                self.add_variable(
                    attr_var.snake_name,
                    DataClassGenerator.get_type_hint(key, value),
                )
        return self

    def from_json(self, json_str):
        return self.from_dict(json.loads(json_str))

    def to_string(self, level=0, with_imports=False):
        indent_str = " " * 4 * level
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

        value_strs = [
            f"{indent_str}    {v.name}: {v.type_hint}" for v in self._variables
        ]

        result_str = (
            "\n".join([class_def_str] + inner_class_strs + value_strs) + "\n"
        )
        if level == 0:
            result_str = re.sub(r"\n{3,}", "\n\n", result_str)
            if with_imports:
                if self.typings:
                    with_imports_str = (
                        "from dataclasses import dataclass\n"
                        f"from typing import {', '.join(self.typings)}\n\n"
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
