from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import tableModel
from database import engine
from routers import talkToMandoAI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")

origins = [
    "http://localhost:4200",  # Angular
    "http://localhost:5173",  # Vite
    "http://localhost:3000",  # CRA/Next dev
    "https://yourdomain.com",  # production
]

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.openai = AsyncOpenAI(api_key=api_key)
    yield
    await app.state.openai.close()


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
