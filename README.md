# 🎮 게임 컬렉션 - Django + Claude AI + 멀티플레이어

Claude AI와 함께하는 지능적인 미니게임 컬렉션입니다. Django 프레임워크를 사용하여 앱 단위로 구조화되어 있으며, 실시간 멀티플레이어 기능과 채팅 시스템을 제공합니다.

## 🚀 주요 기능

- **⚾ 숫자야구**: Claude AI가 생성하는 숫자를 맞춰보세요
- **🔤 끝말잇기**: Claude AI와의 지능적인 끝말잇기
- **🍦 배스킨라빈스31**: Claude AI의 전략적 숫자 선택
- **🎯 고누놀이**: Claude AI와의 틱택토 대결
- **⚫ 오목**: Claude AI와의 15x15 오목 대결
- **👥 멀티플레이어**: 친구들과 함께하는 온라인 게임

## 🌟 멀티플레이어 기능

### 🏠 게임 로비
- **방 생성/참가**: 최대 4명까지 참가 가능한 게임 방
- **별명 시스템**: 각 방에서 고유한 별명 사용
- **방 관리**: 비공개 방, 비밀번호 보호, 방장 권한

### 💬 실시간 채팅
- **방별 채팅**: 각 게임 방에서 독립적인 채팅
- **전역 채팅**: 모든 사용자가 참여할 수 있는 공개 채팅
- **메시지 저장**: 모든 채팅 내용을 데이터베이스에 영구 저장
- **WebSocket 통신**: Django Channels를 사용한 실시간 양방향 통신

### 🎯 게임 통합
- **5가지 게임 지원**: 모든 게임에서 멀티플레이어 모드
- **초대 시스템**: 친구 초대 및 응답 처리
- **게임 기록**: 게임 결과 및 통계 저장

## 🏗️ 프로젝트 구조

```
game_baseball/
├── game_collection/          # 메인 프로젝트 설정
├── baseball/                 # 숫자야구 게임 앱
├── wordchain/               # 끝말잇기 게임 앱
├── baskin31/                # 배스킨라빈스31 게임 앱
├── gonu/                    # 고누놀이 게임 앱
├── omok/                    # 오목 게임 앱
├── multiplayer/             # 멀티플레이어 시스템 앱
├── static/                  # 정적 파일 (CSS, JS)
├── templates/               # HTML 템플릿
├── manage.py                # Django 관리 명령어
├── requirements.txt         # Python 의존성
└── set_env.sh              # 환경 변수 설정 스크립트
```

## 🔧 설치 및 실행

### 1. 의존성 설치

```bash
# Python 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

Claude API 키를 설정해야 합니다:

```bash
# 방법 1: 환경 변수 직접 설정
export CLAUDE_API_KEY="your_api_key_here"

# 방법 2: 스크립트 사용 (권장)
source set_env.sh
```

### 3. 데이터베이스 마이그레이션

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 4. Django 서버 실행

```bash
# 기본 실행
python3 manage.py runserver

# 환경 변수와 함께 실행
source set_env.sh && python3 manage.py runserver

# 모든 IP에서 접근 허용
python3 manage.py runserver 0.0.0.0:8000
```

### 5. Redis 서버 실행 (WebSocket 지원)

```bash
# macOS
brew install redis
redis-server

# Linux
sudo apt-get install redis-server
redis-server
```

## 🌐 접속 URL

- **메인 페이지**: http://localhost:8000/
- **멀티플레이어 로비**: http://localhost:8000/multiplayer/
- **숫자야구**: http://localhost:8000/baseball/
- **끝말잇기**: http://localhost:8000/wordchain/
- **배스킨31**: http://localhost:8000/baskin31/
- **고누놀이**: http://localhost:8000/gonu/
- **오목**: http://localhost:8000/omok/

## 🔑 API 키 설정

### Claude API 키 획득

1. [Anthropic Console](https://console.anthropic.com/)에 접속
2. 계정 생성 및 로그인
3. API 키 생성
4. 생성된 키를 환경 변수에 설정

### 보안 주의사항

- **절대 코드에 API 키를 직접 입력하지 마세요**
- 환경 변수나 `.env` 파일을 사용하세요
- API 키를 Git에 커밋하지 마세요
- 프로덕션 환경에서는 더 안전한 방법을 사용하세요

## 🎯 게임별 특징

### ⚾ 숫자야구
- Claude AI가 전략적으로 숫자 생성
- 3-5자리 숫자 선택 가능
- 실시간 스트라이크/볼 계산
- AI 힌트 시스템

### 🔤 끝말잇기
- Claude AI의 자연스러운 한국어 단어 선택
- 단어 유효성 검증 시스템
- 난이도별 AI 전략
- 재시도 로직

### 🍦 배스킨라빈스31
- Claude AI의 수학적 사고를 활용한 전략
- 승리 확률을 높이는 선택

### 🎯 고누놀이
- Claude AI의 게임 이론 적용
- 최적의 수 계산

### ⚫ 오목
- Claude AI의 패턴 인식 능력
- 15x15 보드에서의 전략적 플레이
- 난이도별 AI 수준

## 🛠️ 개발 환경

- **Python**: 3.8+
- **Django**: 4.2.23
- **Django Channels**: 4.2.2 (WebSocket 지원)
- **Redis**: 6.1+ (채널 레이어)
- **Claude API**: 3.5 Sonnet
- **데이터베이스**: SQLite (개발용)

## 📊 데이터베이스 모델

### 멀티플레이어 시스템
- `GameRoom`: 게임 방 정보
- `RoomPlayer`: 방 참가자 (별명 포함)
- `ChatMessage`: 방별 채팅 메시지
- `GlobalChatMessage`: 전역 채팅 메시지
- `MultiplayerGame`: 멀티플레이어 게임 데이터
- `GameInvitation`: 게임 초대 시스템

### 게임 시스템
- `BaseballGame`: 숫자야구 게임 데이터
- `WordChainGame`: 끝말잇기 게임 데이터
- `OmokGame`: 오목 게임 데이터

## 🚀 배포 정보

### 최신 커밋
- **커밋 해시**: `a5480b0`
- **배포 날짜**: 2024년 12월
- **버전**: 1.0.0

### 구현된 기능
- ✅ Claude AI 통합 게임 5종
- ✅ 실시간 멀티플레이어 시스템
- ✅ WebSocket 기반 채팅
- ✅ 별명 시스템
- ✅ 방 관리 및 초대 시스템
- ✅ 반응형 웹 디자인
- ✅ 데이터베이스 기반 메시지 저장

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

---

**🎮 즐거운 게임 되세요! Claude AI와 함께하는 새로운 게임 경험을 만나보세요!**
