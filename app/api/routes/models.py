"""Models list route."""

from fastapi import APIRouter

from app.application.use_cases.list_models import ListModels
from app.domain.interfaces.model_profile_repository import ModelProfileRepository

router = APIRouter()


def _create_list_models(repo: ModelProfileRepository) -> ListModels:
    return ListModels(model_repo=repo)


@router.get("/v1/models")
async def list_models() -> dict:
    from app.main import get_model_repo
    uc = _create_list_models(get_model_repo())
    models = uc.execute()
    return {
        "object": "list",
        "data": [
            {
                "id": m.id,
                "object": m.object,
                "display_name": m.display_name,
            }
            for m in models
        ],
    }
