from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_concepts():
    return {"concepts": [], "total": 0, "page": 1, "page_size": 20}


@router.get("/{concept_id}")
async def get_concept(concept_id: str):
    return {"id": concept_id, "name": "", "description": "", "prerequisites": []}