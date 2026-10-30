from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class RegisterRequest(Credentials):
    password: str = Field(min_length=10, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    # Only has an effect for signed-in users.
    save: bool = True

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be blank")
        return v


class TokenScore(BaseModel):
    word: str
    # Attention relative to the most-attended word (0..1).
    attention: float


class PredictResponse(BaseModel):
    id: int | None = None
    label: str
    is_sarcastic: bool
    # Probability that the headline is sarcastic.
    probability: float
    # Probability of the predicted class.
    confidence: float
    cleaned_text: str
    tokens: list[TokenScore]
    important_words: list[str]
    warnings: list[str] = []


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    cleaned_text: str
    is_sarcastic: bool
    probability: float
    tokens: list[TokenScore]
    important_words: list[str]
    created_at: datetime


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    total: int


class Stats(BaseModel):
    total: int
    sarcastic: int
    not_sarcastic: int
