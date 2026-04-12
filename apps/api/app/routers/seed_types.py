from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.seed_type import SeedType
from app.schemas.seed_type import SeedTypeResponse

router = APIRouter(tags=["seed-types"])


@router.get("/seed-types", response_model=list[SeedTypeResponse])
async def list_seed_types(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SeedType]:
    result = await db.execute(
        select(SeedType)
        .where(SeedType.is_active.is_(True))
        .order_by(SeedType.sort_order)
    )
    return list(result.scalars().all())
