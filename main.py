from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import tableModel
from database import engine
from routers import talkToMandoAI
from contextlib import asynccontextmanager
import httpx

origins = [
    "http://localhost:4200",  # Angular
    "http://localhost:5173",  # Vite
    "http://localhost:3000",  # CRA/Next dev
    "https://yourdomain.com",  # production
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],  # Authorization, Content-Type, etc
)

tableModel.Base.metadata.create_all(bind=engine)
app.include_router(talkToMandoAI.router, prefix='/api')
