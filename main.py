from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from routers import views_router, email_router, data_router, auth_router, upload_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Plateforme académique démarrée")
    yield

app = FastAPI(
    title="Classe-Etoile -plateforme -academique-ufhb",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(views_router.router)
app.include_router(data_router.router,   prefix="/api")
app.include_router(email_router.router,  prefix="/api")
app.include_router(auth_router.router,   prefix="/api")
app.include_router(upload_router.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
