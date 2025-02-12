from dataclasses import dataclass
import json
import re


class NamingConverter:
    @staticmethod
    def to_lower_camel_case(snake_str):
        return (
            snake_str[0] + NamingConverter.to_upper_camel_case(snake_str)[1:]
        )

    @staticmethod
    def to_upper_camel_case(snake_str):
        return "".join(x.title() for x in snake_str.split("_"))

    @staticmethod
    def to_snake_case(camel_str):
        return "".join(
            ["_" + i.lower() if i.isupper() else i for i in camel_str]
        ).lstrip("_")


class DataClassGenerator:
    @dataclass
    class Value:
        name: str
        type_hint: str

    def __init__(self, name="JsonClass", use_dataclass_json=False):
        name = DataClassGenerator.sanitize_value_name(name)
        self.name = name
        self._inner_classes = []
        self._values = []
        self._use_dataclass_json = use_dataclass_json
        self._typings = []

    def __str__(self):
        inner_classes_str = [
            inner_class.__str__() for inner_class in self._inner_classes
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
    def sanitize_value_name(name):
        return re.sub(r"\W|^(?=\d)", "_", name)

    @staticmethod
    def get_type_hint(key, value):
        print(key, value)
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
            return NamingConverter.to_upper_camel_case(key)
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

    def add_value(self, name, type_hint) -> None:
        name = DataClassGenerator.sanitize_value_name(name)
        if self._values:
            if name in [v.name for v in self._values]:
                del self._values[[v.name for v in self._values].index(name)]
        self._values.append(DataClassGenerator.Value(name, type_hint))
        if "[" in type_hint:
            self._typings.append(type_hint.split("[")[0])

    def from_dict(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                class_name = NamingConverter.to_upper_camel_case(key)
                attribute_name = NamingConverter.to_snake_case(key)
                self.add_inner_class(
                    DataClassGenerator(
                        class_name, self._use_dataclass_json
                    ).from_dict(value)
                )
                self.add_value(attribute_name, class_name)
            else:
                attribute_name = NamingConverter.to_snake_case(key)
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict):
                            class_name = NamingConverter.to_upper_camel_case(
                                key
                            )
                            self.add_inner_class(
                                DataClassGenerator(
                                    class_name, self._use_dataclass_json
                                ).from_dict(v)
                            )
                self.add_value(
                    attribute_name,
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
