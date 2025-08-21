# 🚀 숫자야구 게임 배포 가이드

## 📋 배포 옵션

### 1. 🏠 로컬 네트워크 배포 (가장 간단)

#### 장점
- 무료
- 즉시 실행 가능
- 같은 WiFi 사용자들과 공유 가능

#### 방법
```bash
# 서버 실행
npm start

# 또는 환경변수로 포트 변경
PORT=8080 npm start
```

#### 접속 방법
- **본인**: `http://localhost:3000`
- **같은 WiFi 사용자**: `http://[당신의IP]:3000`

---

### 2. 🐳 Docker 배포

#### 장점
- 환경 독립적
- 확장 가능
- 프로덕션 환경과 유사

#### 방법
```bash
# Docker 이미지 빌드
docker build -t baseball-game .

# 컨테이너 실행
docker run -p 3000:3000 baseball-game

# 백그라운드 실행
docker run -d -p 3000:3000 --name baseball-game baseball-game
```

#### 접속 방법
- `http://localhost:3000`

---

### 3. ☁️ Vercel 배포 (권장)

#### 장점
- 무료
- 자동 HTTPS
- 글로벌 CDN
- 자동 배포

#### 방법
```bash
# Vercel CLI 설치
npm install -g vercel

# 로그인
vercel login

# 배포
vercel --yes
```

#### 접속 방법
- 배포 후 제공되는 URL

---

### 4. 🐙 GitHub Pages + Backend

#### 장점
- 무료
- Git 연동
- 자동 배포

#### 방법
1. GitHub 저장소 생성
2. 코드 푸시
3. GitHub Actions로 자동 배포

---

### 5. 🌐 Netlify 배포

#### 장점
- 무료
- 자동 HTTPS
- 폼 처리 지원

#### 방법
1. Netlify 계정 생성
2. GitHub 저장소 연결
3. 자동 배포 설정

---

## 🔧 환경 설정

### 환경 변수
```bash
# 포트 설정
PORT=3000

# 환경 설정
NODE_ENV=production

# 호스트 설정 (로컬 네트워크용)
HOST=0.0.0.0
```

### 프로덕션 설정
```bash
# 의존성 설치 (프로덕션만)
npm ci --only=production

# 서버 실행
npm start
```

---

## 📱 모바일 접속

### 같은 WiFi 사용자
1. 서버 실행: `npm start`
2. IP 주소 확인 (콘솔에 표시)
3. 모바일에서 `http://[IP]:3000` 접속

### 외부 접속 (포트포워딩)
1. 라우터 설정에서 포트 3000 포워딩
2. 공인 IP로 접속

---

## 🚨 보안 고려사항

### 프로덕션 환경
- HTTPS 사용
- 환경 변수 보호
- 방화벽 설정
- 로그 모니터링

### 로컬 네트워크
- 신뢰할 수 있는 네트워크만 사용
- 방화벽 설정 확인

---

## 🔍 문제 해결

### 포트 충돌
```bash
# 포트 사용 확인
lsof -i :3000

# 다른 포트 사용
PORT=8080 npm start
```

### 방화벽 문제
```bash
# macOS 방화벽 설정
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/node
```

### Docker 문제
```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs baseball-game
```

---

## 📊 모니터링

### 로그 확인
```bash
# 실시간 로그
tail -f logs/app.log

# 에러 로그
grep ERROR logs/app.log
```

### 성능 모니터링
```bash
# 메모리 사용량
ps aux | grep node

# CPU 사용량
top -p $(pgrep node)
```

---

## 🎯 추천 배포 순서

1. **로컬 네트워크** (테스트용)
2. **Vercel** (무료 호스팅)
3. **Docker** (프로덕션 환경)
4. **GitHub Pages** (정적 사이트)

---

## 📞 지원

배포 중 문제가 발생하면:
1. 로그 확인
2. 환경 변수 점검
3. 포트 충돌 확인
4. 방화벽 설정 확인

**즐거운 게임 되세요! ⚾🎮**
