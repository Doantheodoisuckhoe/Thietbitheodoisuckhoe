"""Điểm vào server:  uvicorn app.main:app --reload"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import Base, engine
from .routers import alerts, auth, ingest, patients
from .worker import worker_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # đồ án: tự tạo bảng (sản phẩm thật nên dùng Alembic)
    stop = asyncio.Event()
    task = None
    if get_settings().enable_worker:
        task = asyncio.create_task(worker_loop(stop))
    yield
    stop.set()
    if task:
        await task


app = FastAPI(title="HealthWatch API", version="1.0.0", lifespan=lifespan,
              description="Server giám sát sức khỏe người cao tuổi — nhận dữ liệu, xử lý cảnh báo, push/SMS.")

app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","),
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(ingest.router)
app.include_router(alerts.router)


@app.get("/api/health")
def health():
    return {"ok": True}


_web = get_settings().web_dir
if os.path.isdir(_web):
    app.mount("/dashboard", StaticFiles(directory=_web, html=True), name="dashboard")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/dashboard/")
