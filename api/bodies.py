from pydantic import BaseModel
from pydantic import Field


class Json2DataclassBody(BaseModel):
    class_name: str = Field(default="GeneratedClass", alias="className")
    json_string: str = Field(alias="jsonString")
    with_imports: bool = Field(default=False, alias="withImports")
    use_dataclass_json: bool = Field(default=False, alias="useDataclassJson")
