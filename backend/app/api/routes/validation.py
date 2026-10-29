from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.taxonomy import get_taxonomy_service, TaxonomyService

router = APIRouter()


@router.get("/graph")
async def validate_graph(
    service: Annotated[TaxonomyService, Depends(get_taxonomy_service)] = None,
):
    """Validate prerequisite graph and return quality metrics."""
    return await service.validate_graph()


@router.post("/export")
async def export_taxonomy(
    filepath: str,
    service: Annotated[TaxonomyService, Depends(get_taxonomy_service)] = None,
):
    """Export taxonomy data to JSONL files."""
    try:
        counts = await service.export_to_jsonl(filepath)
        return {"message": "Export successful", "counts": counts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_taxonomy(
    filepath: str,
    service: Annotated[TaxonomyService, Depends(get_taxonomy_service)] = None,
):
    """Import taxonomy data from JSONL files."""
    try:
        counts = await service.import_from_jsonl(filepath)
        return {"message": "Import successful", "counts": counts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
