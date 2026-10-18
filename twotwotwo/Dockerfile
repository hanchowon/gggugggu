# 파이썬 경량화 공식 이미지 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 업데이트 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# Cloud Run에서 제공하는 PORT 환경 변수 사용 (기본값 8080)
ENV PORT=8080

# uvicorn 서버 실행 명령어
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
