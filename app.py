from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import openai
import requests
import os
from dotenv import load_dotenv

# 데이터베이스 관련 import 추가
from database import get_db
from models import Consultation

# Load environment variables
load_dotenv()

# Initialize OpenAI client
from openai import OpenAI

client = OpenAI(api_key=openai.api_key)

# FastAPI app setup
app = FastAPI()

# Vue 정적 파일 서빙
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")


@app.get("/")
async def serve_vue():
    return FileResponse("dist/index.html")


# CORS for frontend local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model for input
class UserInput(BaseModel):
    message: str


# 식약처 API 설정
KEY = "6ea9dc09b54e480995ce"
BASE = "http://openapi.foodsafetykorea.go.kr/api"
SERVICE = "C003"
FMT = "json"


# 성분 이름으로 건강기능식품 검색
def fetch_products_by_ingredient(ingredient):
    start, end = 1, 100
    url = f"{BASE}/{KEY}/{SERVICE}/{FMT}/{start}/{end}"
    try:
        res = requests.get(url, timeout=20)
        res.raise_for_status()
    except requests.exceptions.ReadTimeout:
        return ["⚠️ 식약처 서버 응답이 느립니다. 잠시 후 다시 시도해 주세요."]
    except Exception as e:
        return [f"⚠️ API 호출 중 오류 발생: {e}"]
    items = res.json().get("C003", {}).get("row", [])

    filtered = [
        item for item in items
        if ingredient in item.get("RAWMTRL_NM", "") or ingredient in item.get("PRIMARY_FNCLTY", "")
    ]
    return filtered


# GPT 성분 키워드 추출
EXTRACTION_SYSTEM_PROMPT = (
    "너는 약사야. 사용자 건강 고민에서 건강기능식품 성분만 콤마로 구분해서 추출해줘.\n"
    "없다면 추출하지 마.\n"
    "예시 입력: '요즘 눈이 침침해요' => '루테인, 아스타잔틴'"
)


def extract_keywords(user_input):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3
    )
    content = response.choices[0].message.content.strip()
    return [kw.strip() for kw in content.split(',') if kw.strip()]


# GPT로 설명 요약
def summarize_description(text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "아래 문장을 건강기능식품 약사 설명처럼 간결하게 요약해줘. 큰따옴표 없이."},
            {"role": "user", "content": text}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip().replace('"', '')


# 기존 consult 로직을 별도 함수로 분리
def process_consultation(message):
    keywords = extract_keywords(message)

    if not keywords:
        return {"result": "😥 유의미한 건강기능식품 성분이 추출되지 않았습니다."}

    result = {
        "prescription": f"{', '.join(keywords)} 등의 영양성분의 섭취가 필요해요.",
        "products": []
    }

    shown = set()
    for kw in keywords:
        items = fetch_products_by_ingredient(kw)
        count = 0
        for item in items:
            name = item['PRDLST_NM']
            if name in shown:
                continue
            shown.add(name)
            fnclty = item.get('PRIMARY_FNCLTY', '').strip().replace('\n', ' ').replace('\r', '')
            if not fnclty:
                continue
            short_desc = summarize_description(fnclty)
            result["products"].append({"name": name, "desc": short_desc})
            count += 1
            if count >= 5:
                break

    return result


# 기존 API 엔드포인트 (DB 저장 기능 추가)
@app.post("/consult")
async def consult(user_input: UserInput, db: Session = Depends(get_db)):
    message = user_input.message

    # 기존 상담 로직 실행
    result = process_consultation(message)

    # 결과 메시지 구성
    if result.get("result"):
        final_message = result["result"]
        prescription = ""
    else:
        prescription = result["prescription"]
        product_list = result["products"]

        product_text = ""
        for p in product_list:
            name = p["name"]
            desc = p["desc"]
            # JavaScript 정규표현식을 Python으로 변환
            desc = desc.replace(' - ', '\n  - ')
            desc = desc.replace('①', '\n  ①')
            desc = desc.replace('②', '\n  ②')
            desc = desc.replace('③', '\n  ③')
            desc = desc.replace('④', '\n  ④')
            product_text += f"● {name}\n{desc}\n\n"

        final_message = prescription + '\n\n' + product_text.strip()

    # 데이터베이스에 저장
    try:
        consultation = Consultation(
            user_message=message,
            ai_response=final_message,
            prescription=prescription
        )
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        # 오류가 있어도 응답은 반환

    return result


# 상담 기록 조회 API (새로 추가)
@app.get("/consultations")
async def get_consultations(db: Session = Depends(get_db)):
    try:
        consultations = db.query(Consultation).order_by(
            Consultation.created_at.desc()
        ).all()

        result = []
        for consultation in consultations:
            result.append({
                "id": consultation.id,
                "date": consultation.created_at.strftime("%Y-%m-%d"),
                "time": consultation.created_at.strftime("%H:%M"),
                "userMessage": consultation.user_message,
                "aiResponse": consultation.ai_response,
                "summary": consultation.prescription if consultation.prescription else consultation.user_message[
                                                                                       :50] + "..."
            })

        return result
    except Exception as e:
        print(f"DB 조회 오류: {e}")
        return []


# 상담 기록 삭제 API (새로 추가)
@app.delete("/consultations/{consultation_id}")
async def delete_consultation(consultation_id: int, db: Session = Depends(get_db)):
    try:
        consultation = db.query(Consultation).filter(
            Consultation.id == consultation_id
        ).first()

        if consultation:
            db.delete(consultation)
            db.commit()
            return {"message": "삭제되었습니다."}
        else:
            return {"error": "해당 상담 기록을 찾을 수 없습니다."}, 404
    except Exception as e:
        print(f"DB 삭제 오류: {e}")
        return {"error": "삭제 중 오류가 발생했습니다."}, 500