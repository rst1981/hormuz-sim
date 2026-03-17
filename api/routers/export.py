"""Export endpoints — CSV download."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.schemas import ExportCSVRequest
from api.services.sim_manager import sim_manager, SimNotFoundError

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/csv")
def export_csv(req: ExportCSVRequest):
    try:
        sim = sim_manager._get(req.sim_id)
        csv_data = sim.get_metrics_csv()
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=hormuz_sim_{req.sim_id}.csv"},
        )
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {req.sim_id} not found")
