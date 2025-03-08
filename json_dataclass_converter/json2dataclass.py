from collections import Counter
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
        self._origional_name = name
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
        if re.match(r"^[_0-9-]+$", name):
            return LetterCase.CAMEL
        elif re.match(r"^[_0-9a-z]+$", name):
            return LetterCase.SNAKE
        elif re.match(r"^[_0-9]*[a-z]+(?:[A-Z0-9_-]*[a-z0-9_-]*)*$", name):
            return LetterCase.CAMEL
        elif re.match(r"^[_0-9]*[a-z]+(?:_[a-z0-9]+)*$", name):
            return LetterCase.SNAKE
        elif re.match(r"^[_0-9]*[A-Z]+(?:[A-Z0-9_-]*[a-z0-9_-]*)*$", name):
            return LetterCase.PASCAL
        else:
            print(name)
            raise ValueError("Invalid variable name")

    @property
    def letter_case(self):
        return self._letter_case

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
    def origional_name(self):
        return self._origional_name

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

    def get_name(self, letter_case):
        if letter_case is LetterCase.CAMEL:
            return self.camel_name
        elif letter_case is LetterCase.PASCAL:
            return self.pascal_name
        elif letter_case is LetterCase.SNAKE:
            return self.snake_name

    def __repr__(self):
        return f"Variable(name={self.name!r}, type_hint={self.type_hint!r}, letter_case={self.letter_case})"


class DataClassGenerator:

    _dataclass_json_letter_case_map = {
        LetterCase.CAMEL: "LetterCase.CAMEL",
        LetterCase.PASCAL: "LetterCase.PASCAL",
        LetterCase.SNAKE: "LetterCase.SNAKE",
    }

    def __init__(
        self,
        name="JsonClass",
    ):
        self.name = Variable.sanitize_name(name)
        self._inner_classes = []
        self._variables = []
        self._typings = set()

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
            if not types:
                return "List"
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
            self._typings.add(type_hint.split("[")[0])
        if type_hint == "List":
            self._typings.add(type_hint)

    @property
    def _most_used_letter_case(self):
        if not self._variables:
            return LetterCase.SNAKE
        letter_cases = [i.letter_case for i in self._variables]
        counts = Counter(letter_cases)
        return max(counts, key=lambda x: (counts[x], -letter_cases.index(x)))

    def _handle_list_object_from_dict(self, name, values):
        variable = Variable(name)
        for value in values:
            if isinstance(value, dict):
                self.add_inner_class(
                    DataClassGenerator(variable.pascal_name).from_dict(value)
                )
            elif isinstance(value, list):
                self._handle_list_object_from_dict(name, value)
        self.add_variable(name, DataClassGenerator.get_type_hint(name, values))

    def from_dict(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    class_var = Variable(key)
                    self.add_inner_class(
                        DataClassGenerator(class_var.pascal_name).from_dict(
                            value
                        )
                    )
                    self.add_variable(key, class_var.pascal_name)
                elif isinstance(value, list):
                    self._handle_list_object_from_dict(key, value)
                else:
                    self.add_variable(
                        key,
                        DataClassGenerator.get_type_hint(key, value),
                    )
        elif isinstance(data, list):
            self._handle_list_object_from_dict("top", data)
        return self

    def from_json(self, json_str):
        return self.from_dict(json.loads(json_str))

    @property
    def typings(self):
        all_typings = self._typings.copy()
        for inner_class in self._inner_classes:
            all_typings |= inner_class.typings
        return all_typings

    @property
    def import_dataclasses_field(self):
        for variable in self._variables:
            if (
                Variable(variable.snake_name).get_name(
                    self._most_used_letter_case
                )
                != variable.origional_name
            ):
                return True
        for inner_class in self._inner_classes:
            for variable in inner_class._variables:
                if (
                    Variable(variable.snake_name).get_name(
                        self._most_used_letter_case
                    )
                    != variable.origional_name
                ):
                    return True
        return False

    @property
    def import_dataclasses_json_lettercase(self):
        if self._most_used_letter_case != LetterCase.SNAKE:
            return True
        else:
            return False

    @property
    def import_dataclasses_json_lettercase(self):
        if self._most_used_letter_case != LetterCase.SNAKE:
            return True
        else:
            return False

    def to_string(self, level=0, with_imports=False, use_dataclass_json=False):
        indent_str = " " * 4 * level
        class_def_str = (
            f"\n{indent_str}@dataclass\n{indent_str}class {self.name}:"
        )
        if use_dataclass_json:
            if self._most_used_letter_case == LetterCase.SNAKE:
                class_def_str = (
                    f"\n{indent_str}@dataclass_json" + class_def_str
                )
            else:
                class_def_str = (
                    f"\n{indent_str}@dataclass_json(letter_case="
                    f"{self._dataclass_json_letter_case_map[self._most_used_letter_case]})"
                    + class_def_str
                )
        inner_class_strs = [
            inner_class.to_string(
                level + 1, use_dataclass_json=use_dataclass_json
            )
            for inner_class in self._inner_classes
        ]

        if self._variables:
            value_strs = []
            for variable in self._variables:
                if (
                    Variable(variable.snake_name).get_name(
                        self._most_used_letter_case
                    )
                    != variable.origional_name
                ):
                    field_str = f'field(metadata=config(field_name="{variable.origional_name}"))'
                    value_str = f"{indent_str}    {variable.snake_name}: {variable.type_hint} = {field_str}"
                else:
                    value_str = f"{indent_str}    {variable.snake_name}: {variable.type_hint}"
                value_strs.append(value_str)
        else:
            value_strs = [f"{indent_str}    pass"]

        result_str = (
            "\n".join([class_def_str] + inner_class_strs + value_strs) + "\n"
        )
        if level == 0:
            result_str = re.sub(r"\n{3,}", "\n\n", result_str)
            if with_imports:
                with_imports_str = "from dataclasses import dataclass"
                if self.import_dataclasses_field:
                    with_imports_str += ", field"
                with_imports_str += "\n"
                if self.typings:
                    with_imports_str += (
                        f"from typing import {', '.join(self.typings)}\n"
                    )
                with_imports_str += "\n"
                if use_dataclass_json:
                    with_imports_str += (
                        "from dataclasses_json import dataclass_json"
                    )
                    if self.import_dataclasses_json_lettercase:
                        with_imports_str += ", LetterCase"
                    with_imports_str += "\n\n"
                return with_imports_str + result_str
            else:
                return result_str.lstrip("\n")
        return result_str
