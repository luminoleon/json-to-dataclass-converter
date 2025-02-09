# JSON to Dataclass Converter

###### [简体中文](/README.md) | [English](/docs/en/README.md)

网站：https://json2dataclass.luminoleon.top

`JSON to dataclass Converter` 是一个用于将 JSON 数据转换为 Python 数据类的工具。它可以帮助开发者快速生成数据类，简化数据处理和验证的工作。

## 本地运行步骤

1.  克隆本项目
    ```Powershell
    git clone https://github.com/luminoleon/json-to-dataclass-converter.git
    cd json-to-dataclass-converter
    ```
2. 安装[Python3](https://www.python.org/downloads/)
3. 安装依赖
    ```Powershell
    pip install -r requirements.txt
    ```
4. 执行脚本
    ```Powershell
    fastapi run
    ```

## 效果示例

JSON数据示例：

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

转换后的效果：

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

## 贡献

`JSON to Dataclass Converter` 使用 MIT 许可证。有关更多信息，请参阅 [LICENSE](LICENSE) 文件。
欢迎提交任何issue或pull requests.
