from fastapi import APIRouter, Depends

from app.api.http.dependencies import Container, get_container

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready(container: Container = Depends(get_container)) -> dict:
    container.check_database()  # raises ServiceUnavailable -> 503
    return {"status": "ready"}
