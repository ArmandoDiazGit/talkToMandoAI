import os
from typing import Annotated, Optional
from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from tableModel import TalkToMandoAI
from starlette import status
from dotenv import load_dotenv
import httpx

load_dotenv()
router = APIRouter()

api_key = os.getenv("OPENAI_API_KEY")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class TalkToMandoAIRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = "google/gemma-3-4b-it"
    temperature: float = 0.7
    max_tokens: int = 512


class TalkToMandoAIResponse(BaseModel):
    prompt: str
    answer: str


@router.get('/prompts', status_code=status.HTTP_200_OK)
async def get_prompts(db: db_dependency):
    return db.query(TalkToMandoAI).all()


@router.post('/generate')
async def generate(body: TalkToMandoAIRequest, request: Request):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Missing API key')
    client: httpx.AsyncClient = request.app.state.http

    url = "https://api.aimlapi.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": body.model,
        "messages": [{"role": "user", "content": body.prompt.strip()}],
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
    }

    try:
        resopnse = await client.post(url, headers=headers, json=payload)
        resopnse.raise_for_status()
        data = resopnse.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream request timed out")
    except httpx.HTTPStatusError:
        try:
            err = resopnse.json()
        except Exception:
            err = {"status_code": resopnse.status_code, "text": resopnse.text}
        raise HTTPException(status_code=502, detail={"upstream_error": err})
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e}")

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail={"message": "Unexpected upstream response shape", "raw": data})

    return TalkToMandoAIResponse(prompt=body.prompt, answer=answer)
