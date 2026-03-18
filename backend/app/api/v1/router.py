from fastapi import APIRouter

from app.api.v1 import datasets, evaluations, models, results, tasks

api_router = APIRouter()
api_router.include_router(models.router)
api_router.include_router(datasets.router)
api_router.include_router(evaluations.router)
api_router.include_router(results.router)
api_router.include_router(tasks.router)
