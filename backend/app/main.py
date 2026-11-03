from fastapi import FastAPI

from .errors import install_handlers
from .routers import approvals, auth, dashboard, drawings, hulls, me, plans, progress, users, weather


def create_app() -> FastAPI:
    app = FastAPI(title="SWP Shipyard API", version="0.1.0")
    install_handlers(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(me.router)
    app.include_router(users.router)
    app.include_router(users.groups_router)
    app.include_router(hulls.router)
    app.include_router(plans.router)
    app.include_router(progress.router)
    app.include_router(drawings.router)
    app.include_router(approvals.router)
    app.include_router(dashboard.router)
    app.include_router(weather.router)
    return app


app = create_app()
