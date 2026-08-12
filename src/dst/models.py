from pydantic import BaseModel


class DSTQuery(BaseModel):
    table_id: str
    variables: dict[str, list[str]]
