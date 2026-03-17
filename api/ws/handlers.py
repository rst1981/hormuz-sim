"""WebSocket handlers for MC streaming and live simulation."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.services.sim_manager import sim_manager, SimNotFoundError
from api.services.mc_runner import mc_runner

router = APIRouter()


@router.websocket("/ws/mc/{job_id}")
async def ws_mc_stream(websocket: WebSocket, job_id: str):
    """Stream Monte Carlo run results as they complete."""
    await websocket.accept()

    async def on_event(event_type: str, data, completed: int, total: int):
        try:
            if event_type == "run_complete":
                await websocket.send_json({
                    "type": "run_complete",
                    "run_id": data["run_id"],
                    "data": data,
                })
                await websocket.send_json({
                    "type": "progress",
                    "completed": completed,
                    "total": total,
                })
            elif event_type == "job_complete":
                await websocket.send_json({
                    "type": "job_complete",
                    "data": data,
                })
        except Exception:
            pass

    mc_runner.add_listener(job_id, on_event)

    try:
        # Keep connection alive; handle client cancel messages
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=30)
                if msg.get("type") == "cancel":
                    mc_runner.cancel(job_id)
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    status = mc_runner.get_status(job_id)
                    await websocket.send_json({"type": "heartbeat", **status})
                    if status["status"] in ("completed", "cancelled", "failed"):
                        break
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        mc_runner.remove_listener(job_id, on_event)


@router.websocket("/ws/sim/{sim_id}/live")
async def ws_live_sim(websocket: WebSocket, sim_id: str):
    """Live simulation stepping via WebSocket."""
    await websocket.accept()

    auto_running = False
    auto_interval = 1.0

    try:
        while True:
            if auto_running:
                try:
                    msg = await asyncio.wait_for(websocket.receive_json(), timeout=auto_interval)
                except asyncio.TimeoutError:
                    msg = {"type": "step"}  # auto-step on timeout
            else:
                msg = await websocket.receive_json()

            msg_type = msg.get("type", "")

            if msg_type == "step":
                try:
                    report = sim_manager.step(sim_id)
                    await websocket.send_json({"type": "turn", "data": report})

                    if report["termination_status"] != "continuing":
                        state = sim_manager.get_state(sim_id)
                        await websocket.send_json({
                            "type": "terminated",
                            "outcome": report["termination_status"],
                            "final_state": state,
                        })
                        auto_running = False
                except SimNotFoundError:
                    await websocket.send_json({"type": "error", "message": "Sim not found"})
                    break

            elif msg_type == "auto":
                auto_running = True
                auto_interval = msg.get("interval_ms", 1000) / 1000.0

            elif msg_type == "pause":
                auto_running = False

    except WebSocketDisconnect:
        pass
