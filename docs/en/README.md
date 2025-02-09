# JSON to Dataclass Converter

###### [简体中文](/README.md) | [English](/docs/en/README.md)

Website: https://json2dataclass.luminoleon.top

`JSON to Dataclass Converter` is a tool for converting JSON data into Python data classes. It helps developers quickly generate data classes, simplifying data processing and validation.

## Local Setup

1. Clone the repository
    ```Powershell
    git clone https://github.com/luminoleon/json-to-dataclass-converter.git
    cd json-to-dataclass-converter
    ```
2. Install [Python3](https://www.python.org/downloads/)
3. Install dependencies
    ```Powershell
    pip install -r requirements.txt
    ```
4. Run the script
    ```Powershell
    fastapi run
    ```

## Example

JSON data example:

```JSON
{
    "name": "John",
    "age": 30,
    "email": "john.doe@example.com",
    "address": {
        "street": "123 Main St",
        "city": "Anytown",
        "zipcode": "12345"
    }
}
```

Converted result:

```Python
from dataclasses import dataclass

from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class JsonClass:

    @dataclass_json(letter_case=LetterCase.CAMEL)
    @dataclass
    class Address:
        street: str
        city: str
        zipcode: str

    name: str
    age: int
    email: str
    address: Address
```

## Contribution

`JSON to Dataclass Converter` is licensed under the MIT License. For more information, please refer to the [LICENSE](LICENSE) file.
Feel free to submit any issues or pull requests.
