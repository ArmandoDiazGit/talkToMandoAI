import os
from typing import Annotated, Optional, Any

import httpx

from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from tableModel import TalkToMandoAI
from starlette import status
from dotenv import load_dotenv
import re
import openai

load_dotenv()
router = APIRouter()

api_key = os.getenv("OPENAI_API_KEY")

AIML_URL = "https://api.aimlapi.com/v1/chat/completions"


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
    response: str


class GenerateOpenAIRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = "gpt-5.2"
    temperature: float = 0.7
    max_output_tokens: int = 512


class GenerateOpenAIResponse(BaseModel):
    output_text: str
    request_id: str | None = None


@router.get('/prompts', status_code=status.HTTP_200_OK)
async def get_prompts(db: db_dependency):
    return db.query(TalkToMandoAI).all()


COMMENT_WRAP_RE = re.compile(r"^\s*/\*+(.*?)\*+/\s*$", re.DOTALL)
LINE_PREFIX_RE = re.compile(r"(?m)^\s*(?:\*+|/+)\s+")


def _safe_json(resp: httpx.Response) -> Any | None:
    try:
        return resp.json()
    except ValueError:
        return None


def clean_ai_text(text: str) -> str:
    t = (text or "").strip()

    m = COMMENT_WRAP_RE.match(t)
    if m:
        t = m.group(1).strip()

    t = LINE_PREFIX_RE.sub("", t)

    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    return t


@router.post("/generate-AIML")
async def generate(body: TalkToMandoAIRequest, request: Request):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing API key",
        )

    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    client: httpx.AsyncClient = request.app.state.http  # lifespan-created client

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": body.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
    }

    try:
        resp = await client.post(AIML_URL, headers=headers, json=payload)
        resp.raise_for_status()

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        answer = clean_ai_text(answer)

        return TalkToMandoAIResponse(prompt=body.prompt, response=answer)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream request timed out")

    except httpx.HTTPStatusError as exc:
        upstream = exc.response
        detail = _safe_json(upstream) or {"status_code": upstream.status_code, "text": upstream.text}
        raise HTTPException(status_code=upstream.status_code, detail=detail)

    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc!s}")

    except (KeyError, IndexError, TypeError, ValueError):
        # ValueError covers json decode issues too
        raise HTTPException(
            status_code=502,
            detail={"message": "Unexpected upstream response shape"},
        )


@router.post("/generateOpenAI", response_model=GenerateOpenAIResponse)
async def generate(body: GenerateOpenAIRequest, request: Request):
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    client = request.app.state.openai

    try:
        resp = await client.responses.create(
            model=body.model,
            input=prompt,
            temperature=body.temperature,
            max_output_tokens=body.max_output_tokens,
        )
        return GenerateOpenAIResponse(
            output_text=resp.output_text,
            request_id=getattr(resp, "_request_id", None),
        )

    except openai.RateLimitError:
        raise HTTPException(429, "OpenAI rate limit hit. Try again shortly.")
    except openai.APIConnectionError:
        raise HTTPException(504, "Could not reach OpenAI (network/timeout).")
    except openai.APIStatusError as e:
        raise HTTPException(e.status_code, f"OpenAI error: {str(e)}")
