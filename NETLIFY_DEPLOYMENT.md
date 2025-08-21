# 🌐 Netlify 배포 가이드

## 📋 Netlify 배포 단계

### 1. **GitHub 저장소 준비**

```bash
# 현재 변경사항 커밋
git add .
git commit -m "Netlify 배포 준비 완료"

# GitHub에 푸시
git push origin master
```

### 2. **Netlify 계정 생성**

1. [Netlify](https://netlify.com) 접속
2. "Sign up" 클릭
3. GitHub 계정으로 로그인

### 3. **새 사이트 배포**

1. **"New site from Git"** 클릭
2. **GitHub** 선택
3. **저장소 선택**: `game_baseball`
4. **브랜치 선택**: `master`
5. **빌드 설정**:
   - **Build command**: `npm run build`
   - **Publish directory**: `public`
   - **Functions directory**: `netlify/functions`

### 4. **환경 변수 설정**

Netlify 대시보드에서:
1. **Site settings** → **Environment variables**
2. 다음 변수 추가:
   ```
   NODE_VERSION = 18
   NODE_ENV = production
   ```

### 5. **Functions 설정**

1. **Site settings** → **Functions**
2. **Functions directory**: `netlify/functions`
3. **Node bundler**: `esbuild`

### 6. **배포 확인**

1. **Deploys** 탭에서 배포 상태 확인
2. **Functions** 탭에서 함수 상태 확인
3. 제공된 URL로 접속 테스트

---

## 🔧 기술적 세부사항

### Netlify Functions 구조
```
netlify/
└── functions/
    └── socket.js          # 게임 로직 처리
```

### API 엔드포인트
- **게임 시작**: `POST /.netlify/functions/socket`
  - Action: `startAIGame`
  - Data: `{ digitCount: 3, playerId: "..." }`

- **추측 제출**: `POST /.netlify/functions/socket`
  - Action: `makeGuess`
  - Data: `{ gameId: "...", guess: [1,2,3], playerId: "..." }`

### 클라이언트 변경사항
- Socket.IO → Netlify Functions API 호출
- 실시간 통신 → HTTP 요청/응답
- 플레이어 ID 자동 생성

---

## 🚀 배포 후 테스트

### 1. **기본 기능 테스트**
- [ ] 메인 메뉴 로드
- [ ] 자릿수 선택 (3자리/4자리)
- [ ] AI 게임 시작
- [ ] 숫자 입력 및 제출
- [ ] 결과 표시 (S, B, O)
- [ ] 게임 종료 및 결과

### 2. **에러 처리 테스트**
- [ ] 잘못된 입력 처리
- [ ] 중복 숫자 입력
- [ ] 빈 값 입력
- [ ] 네트워크 오류

### 3. **모바일 테스트**
- [ ] 반응형 디자인
- [ ] 터치 입력
- [ ] 화면 크기별 레이아웃

---

## 🔍 문제 해결

### 일반적인 문제들

#### 1. **Functions 404 에러**
```bash
# netlify.toml 확인
[functions]
  directory = "netlify/functions"
```

#### 2. **빌드 실패**
```bash
# package.json 스크립트 확인
"build": "echo 'Build completed'"
```

#### 3. **CORS 오류**
```javascript
// socket.js에서 CORS 헤더 확인
const headers = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
};
```

#### 4. **환경 변수 문제**
- Netlify 대시보드에서 환경 변수 재설정
- 배포 후 캐시 클리어

---

## 📱 모바일 최적화

### PWA 설정 (선택사항)
```json
// public/manifest.json
{
  "name": "숫자야구 게임",
  "short_name": "야구게임",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#667eea"
}
```

### 모바일 메타 태그
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
```

---

## 🎯 성능 최적화

### 1. **Functions 최적화**
- 코드 분할
- 메모리 사용량 최소화
- 응답 시간 개선

### 2. **클라이언트 최적화**
- 이미지 압축
- CSS/JS 압축
- 캐싱 전략

### 3. **CDN 활용**
- Netlify의 글로벌 CDN 자동 적용
- 정적 자산 최적화

---

## 🔒 보안 고려사항

### 1. **API 보안**
- 입력 검증 강화
- Rate limiting 고려
- 에러 메시지 보안

### 2. **환경 변수**
- 민감한 정보는 환경 변수로 관리
- Git에 커밋하지 않음

### 3. **CORS 설정**
- 프로덕션에서는 특정 도메인만 허용
- 개발 환경에서만 `*` 사용

---

## 📊 모니터링

### Netlify 대시보드
- **Analytics**: 방문자 통계
- **Functions**: 함수 실행 통계
- **Deploys**: 배포 히스토리
- **Forms**: 폼 제출 통계

### 로그 확인
```bash
# Functions 로그
netlify functions:logs

# 사이트 로그
netlify logs
```

---

## 🎉 배포 완료 후

### 1. **URL 공유**
- Netlify에서 제공하는 URL
- 커스텀 도메인 설정 (선택사항)

### 2. **사용자 피드백 수집**
- 게임 플레이 경험
- UI/UX 개선점
- 버그 리포트

### 3. **지속적 개선**
- 정기적인 업데이트
- 새로운 기능 추가
- 성능 최적화

---

## 📞 지원

### Netlify 공식 지원
- [Documentation](https://docs.netlify.com)
- [Community](https://community.netlify.com)
- [Support](https://www.netlify.com/support/)

### 프로젝트 관련
- GitHub Issues
- 코드 리뷰
- 기술 문서

---

**즐거운 배포 되세요! 🚀⚾**
