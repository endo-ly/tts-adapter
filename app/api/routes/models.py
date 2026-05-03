"""Models list route."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_model_repo
from app.application.use_cases.list_models import ListModels
from app.infrastructure.repositories.yaml_model_profile_repository import YamlModelProfileRepository

router = APIRouter()


@router.get("/v1/models")
async def list_models(
    repo: YamlModelProfileRepository = Depends(get_model_repo),
) -> dict:
    uc = ListModels(model_repo=repo)
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
