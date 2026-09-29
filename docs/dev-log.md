# Development Log

## FREE-001 — Foundation

### Goal

FreeStack의 Frontend와 Backend가 로컬에서 실행되고, Frontend가 Backend `GET /health`를 호출해 연결 상태를 표시하는 최소 기반을 만든다. 도메인, 추천, 데이터베이스, 인증, 배포는 포함하지 않는다.

### Decisions

- 저장소는 기존 dashboard와 분리한 `d:\free-stack` 모노레포로 둔다. FreeStack은 별도 제품이고, dashboard 저장소에 섞으면 범위가 달라진다.
- Python 패키지는 `backend/src/freestack` src layout으로 두고, 의존성은 `uv`와 `pyproject.toml`로 관리한다. runtime은 FastAPI와 Uvicorn, 개발 의존성은 pytest와 httpx다.
- CORS 허용 origin은 `CORS_ALLOWED_ORIGINS` 환경변수만 사용한다. 코드에 localhost origin을 하드코딩하지 않고, 개발용 값은 `backend/.env.example`에 둔다. settings 라이브러리는 추가하지 않고 `os.environ`으로 읽는다. 실행 시 `uv run --env-file .env`가 값을 프로세스 환경에 넣는다.
- httpx 0.28의 `ASGITransport`는 비동기 전용이다. 테스트는 `httpx.AsyncClient`와 pytest의 anyio 마커로 작성한다. anyio는 FastAPI가 이미 가져오므로 테스트용 의존성을 추가하지 않는다.
- Frontend 개발 서버는 포트 5173과 `strictPort`를 사용한다. API base URL은 `VITE_API_BASE_URL`만 사용한다.
- 화면은 연결 상태 문장만 보여 준다. 추천 UI나 도메인 모델은 만들지 않는다.

### Implemented

- Backend: `create_app()`, `GET /health` (`HealthResponse`, 200, `{"status":"ok"}`), 환경변수 기반 CORS.
- Frontend: Vite React TypeScript 앱, `getHealth()`, 마운트 시 health 호출, Checking / OK / Connection Failed 표시.
- 환경 예시: `backend/.env.example`, `frontend/.env.example`. 실제 `.env`는 gitignore.
- 문서: `README.md`, `AGENTS.md`, 이 로그.

### Tests

- Backend: `uv run pytest` — 4 passed.
  - `/health`가 200과 `{"status":"ok"}`를 반환한다.
  - `http://localhost:5173` 허용, `http://127.0.0.1:5173` preflight 허용, 그 외 origin은 허용하지 않는다.
- Frontend: `npm test` (`vitest run`) — 2 passed.
  - health 성공 시 `Backend Status: OK`.
  - health 실패 시 `Backend Status: Connection Failed`.
- 실행 확인: Backend `http://127.0.0.1:8000`, Frontend `http://localhost:5173`.
  - `GET /health` 응답은 `200`과 `{"status":"ok"}`이고, `Origin: http://localhost:5173`에 대해 `access-control-allow-origin`이 같은 origin이다.
  - 브라우저에서 Frontend가 `Backend Status: OK`를 표시했다.

### Notes

- `VITE_` 환경변수는 브라우저 번들에 들어간다. secret을 넣지 않는다.
- `python-dotenv`는 Uvicorn standard extra의 전이 의존성으로 설치된다. 애플리케이션 코드는 이 패키지를 직접 호출하지 않는다.
- 이번 Task에서 Database, Supabase, Provider, Service, Plan, Capability, Limit, Recommendation, AI, Login, Deployment, Docker, CI는 구현하지 않았다.

## FREE-002 — Provider Domain

### Goal

인프라 서비스를 제공하는 사업자/플랫폼을 `Provider` 도메인 모델로 표현하고 테스트한다. 저장, 조회, API, 시드 데이터는 만들지 않는다.

### Design

`Provider`는 `id`, `name`, `slug`, `description` 네 문자열 필드만 가진다.

- `id`는 이 모델 안의 식별자다. 데이터베이스 ID가 아니다.
- `name`은 사용자에게 보여줄 이름이다.
- `slug`는 URL이나 내부 참조에 쓸 안정적인 문자열 식별자다.
- `description`은 짧은 설명 문자열이다.

모델은 자신의 상태만 표현한다. 저장, 검색, 수정, 삭제, 검증 서비스는 포함하지 않는다.

### Decisions

- Domain Model로 분리한다. Provider는 API 응답이나 테이블 행이 아니라 비즈니스 개념이다. FastAPI 계층과 붙이면 이후 API 변경이 도메인 의미를 바꾸게 된다.
- 구현은 Python `dataclass`다. 표준 라이브러리만으로 필드와 불변성을 표현할 수 있다.
- Pydantic은 쓰지 않는다. Pydantic은 이번 기반의 API 응답 모델에 쓰이고 있고, 도메인 모델과 요청/응답 모델을 같은 타입으로 두면 경계가 사라진다.
- 검토한 다른 방식은 일반 클래스와 Pydantic 모델이다. 일반 클래스는 필드 선언이 장황하고, Pydantic은 API 계층과 결합된다. `frozen=True, slots=True` dataclass가 이번 범위에 맞다.
- Repository와 Database는 제외한다. 이번 Task의 목적은 개념을 코드와 테스트로 고정하는 것이다. 저장 구조는 저장이 필요한 Task에서 따로 설계한다.
- 빈 문자열, slug 형식, description 길이 검증은 넣지 않는다. 검증 라이브러리나 도메인 서비스로 범위를 넓히지 않기 위해서다.

### Implemented

- `backend/src/freestack/domain/provider.py`: immutable `Provider` dataclass.
- `backend/src/freestack/domain/__init__.py`: domain 패키지 초기화.
- `backend/tests/test_provider.py`: 생성, 필드, 불변성 테스트.

### Tests

- `uv run pytest` — 7 passed.
  - 기존 health 테스트 4개 통과.
  - Provider 생성, 필드 값, 불변성 테스트 3개 통과.

### Notes

- 테스트의 Cloudflare 예시는 모델이 문자열을 받는다는 것을 보여주는 값이다. Provider 시드 데이터가 아니다.
- API, Repository, CRUD, Frontend, Recommendation은 구현하지 않았다.

