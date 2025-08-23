# Python 3.8 베이스 이미지 사용
FROM python:3.8-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 정적 파일 수집
RUN python3 manage.py collectstatic --noinput

# 포트 노출
EXPOSE 8000

# 환경변수 설정
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=game_collection.settings

# 애플리케이션 실행
CMD ["gunicorn", "game_collection.wsgi:application", "--bind", "0.0.0.0:8000"]
