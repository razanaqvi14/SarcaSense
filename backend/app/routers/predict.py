from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_optional_user
from ..ml.predictor import EmptyTextError
from ..models import Prediction, User
from ..ratelimit import limiter
from ..schemas import PredictRequest, PredictResponse, TokenScore

router = APIRouter(prefix="/api", tags=["predict"])
_settings = get_settings()


@router.post("/predict", response_model=PredictResponse)
@limiter.limit(_settings.rate_limit_predict)
def predict(
    request: Request,
    body: PredictRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if len(body.text) > _settings.max_text_length:
        raise HTTPException(
            422,
            f"Text must be at most {_settings.max_text_length} characters",
        )

    try:
        result = request.app.state.predictor.predict(body.text)
    except EmptyTextError as exc:
        raise HTTPException(422, str(exc))

    tokens = [TokenScore(word=w, attention=round(a, 4)) for w, a in result.tokens]
    saved_id = None
    if user is not None and body.save:
        row = Prediction(
            user_id=user.id,
            text=body.text,
            cleaned_text=result.cleaned_text,
            is_sarcastic=result.is_sarcastic,
            probability=result.probability,
            tokens=[t.model_dump() for t in tokens],
            important_words=result.important_words,
        )
        db.add(row)
        db.commit()
        saved_id = row.id

    p = result.probability
    return PredictResponse(
        id=saved_id,
        label="Sarcastic" if result.is_sarcastic else "Not Sarcastic",
        is_sarcastic=result.is_sarcastic,
        probability=p,
        confidence=p if result.is_sarcastic else 1 - p,
        cleaned_text=result.cleaned_text,
        tokens=tokens,
        important_words=result.important_words,
        warnings=result.warnings,
    )
