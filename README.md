# FreeStack

FreeStack은 사용자가 입력한 프로젝트 조건을 바탕으로 무료 또는 저비용 인프라 조합을 추천하는 서비스다.

이번 저장소는 그 추천 기능을 만들기 전의 최소 실행 기반이다. Frontend와 Backend가 서로 통신할 수 있는 상태만 제공한다.

## 기술 스택

| 영역 | 도구 |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI, Uvicorn |
| Frontend test | Vitest, React Testing Library |
| Backend test | pytest, httpx |
| Python dependency | uv |

## 프로젝트 구조

```text
free-stack/
├── backend/          # FastAPI 애플리케이션 (src layout)
├── frontend/         # React + Vite 애플리케이션
├── docs/dev-log.md   # 구현 결정과 검증 기록
├── AGENTS.md         # AI Agent 작업 규칙
└── README.md
```

## 실행 방법

개발 서버 주소는 고정한다.

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

### Backend

`uv`가 설치되어 있어야 한다. [uv 설치 문서](https://docs.astral.sh/uv/getting-started/installation/)를 따른다.

```powershell
cd backend
copy .env.example .env
uv sync
uv run --env-file .env uvicorn freestack.main:app --reload --host 127.0.0.1 --port 8000
```

Backend는 프로세스 환경변수만 읽는다. 별도 settings 라이브러리는 사용하지 않는다. `uv run --env-file .env`가 `.env`의 값을 실행 환경에 넣는다.

테스트:

```powershell
cd backend
uv run pytest
```

### Frontend

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Vite 개발 서버는 포트 `5173`을 사용하고, 해당 포트를 다른 포트로 바꾸지 않는다.

테스트:

```powershell
cd frontend
npm test
```

## Health API

Backend 생존 확인용 endpoint다.

```text
GET /health
```

응답 `200 OK`:

```json
{
  "status": "ok"
}
```

예:

```powershell
curl http://127.0.0.1:8000/health
```

Frontend는 앱이 마운트되면 이 endpoint를 호출하고 화면에 연결 상태를 표시한다.

- 확인 중: `Backend Status: Checking...`
- 성공: `Backend Status: OK`
- 실패: `Backend Status: Connection Failed`

## Environment

실제 비밀값이 들어 있는 `.env`는 커밋하지 않는다. 각 앱의 `.env.example`을 복사해서 로컬 `.env`를 만든다.

### Frontend `frontend/.env.example`

```env
VITE_API_BASE_URL=http://localhost:8000
```

`VITE_`로 시작하는 값은 브라우저 번들에 포함된다. 이 변수에는 secret을 넣지 않는다.

### Backend `backend/.env.example`

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

CORS 허용 origin은 이 환경변수로만 정한다. Python 코드에 origin을 하드코딩하지 않는다.
