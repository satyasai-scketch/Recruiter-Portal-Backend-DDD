from pydantic import BaseModel


class JDCreate(BaseModel):
	title: str
	original_text: str


class JDRead(BaseModel):
	id: str
	title: str
	original_text: str
	refined_text: str | None = None
