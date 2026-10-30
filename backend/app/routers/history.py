from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Prediction, User
from ..schemas import HistoryPage, Stats

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryPage)
def list_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = Prediction.user_id == user.id
    total = db.scalar(select(func.count()).select_from(Prediction).where(base)) or 0
    items = db.scalars(
        select(Prediction)
        .where(base)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return HistoryPage(items=items, total=total)


@router.get("/stats", response_model=Stats)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total, sarcastic = db.execute(
        select(
            func.count(),
            func.coalesce(func.sum(case((Prediction.is_sarcastic, 1), else_=0)), 0),
        ).where(Prediction.user_id == user.id)
    ).one()
    return Stats(total=total, sarcastic=int(sarcastic), not_sarcastic=total - int(sarcastic))


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_one(
    prediction_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Scoped to the owner, so another user's id looks exactly like a missing one.
    result = db.execute(
        delete(Prediction).where(
            Prediction.id == prediction_id, Prediction.user_id == user.id
        )
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(delete(Prediction).where(Prediction.user_id == user.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
