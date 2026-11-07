from fastapi import APIRouter, Request, Response

from app.observability.metrics import ObservabilityMetrics

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    registry: ObservabilityMetrics = request.app.state.observability_metrics
    body, content_type = registry.render()
    return Response(content=body, headers={"Content-Type": content_type})
