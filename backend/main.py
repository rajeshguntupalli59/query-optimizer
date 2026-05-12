from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import connections, explain, indexes, slow_queries, rewriter, ai, license as license_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="QueryOptimizer",
    version="1.0.0",
    description="Self-hosted SQL query optimization workbench for DBAs",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connections.router)
app.include_router(explain.router)
app.include_router(indexes.router)
app.include_router(slow_queries.router)
app.include_router(rewriter.router)
app.include_router(ai.router)
app.include_router(license_router.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
