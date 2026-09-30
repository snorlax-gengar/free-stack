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

## FREE-003 — Service / Plan Domain

### Goal

카탈로그의 다음 단위인 Service와 Plan을 도메인 모델로 추가하고, Provider를 같은 규칙으로 맞춘다. 저장, API, 시드 데이터는 만들지 않는다.

### Design

관계는 객체를 중첩하지 않고 ID로만 표현한다.

```text
Provider
    │ provider_id
    ▼
Service
    │ service_id
    ▼
Plan
```

- `id`: 전역 식별자. 생성 후 바꾸지 않는다. 문자열을 파싱해 관계를 추론하지 않는다.
- `slug`: 사람이 읽고 URL에 쓸 식별자. Provider slug는 전역, Service slug는 같은 Provider 안, Plan slug는 같은 Service 안에서 고유하다는 의미만 가진다. 모델은 그 중복을 검사하지 않는다.
- `name`: 표시용 이름.
- `description`: 설명. 빈 문자열을 허용한다.

Service는 Plan이 독립적으로 붙는 제품 단위다. Plan은 한 Service의 이용 조건 묶음이다.

세 모델 모두 `frozen=True, slots=True, kw_only=True` dataclass다.

### Decisions

- FREE-002는 검증을 일부러 넣지 않았다. 이번 설계 리뷰에서 ID, slug, name의 최소 형식 검사가 도메인 자신의 책임으로 정해져 그 범위만 추가했다.
- 같은 정규식과 name 검사를 `domain/validation.py`에 둔다. Provider, Service, Plan이 규칙을 각각 복사하지 않게 하기 위해서다. Pydantic이나 외부 검증 라이브러리는 쓰지 않는다.
- `NewType`은 만들지 않는다. 타입 체커를 실행하지 않으므로 `kw_only=True`로 인자 순서를 막는다.
- 가격, 무료 여부, capability, limit은 넣지 않는다. 실제 Provider 조건을 조사하기 전에 필드를 고정하면 잘못된 모델이 된다.
- name은 앞뒤 공백을 제거해 비었는지만 본다. 내용이 있으면 입력 문자열을 그대로 저장한다. 값을 조용히 고치지 않기 위해서다.
- 검토한 다른 방식은 Provider.services, Service.plans처럼 객체를 중첩하는 것이다. 중첩은 카탈로그 조회와 수명 주기를 도메인 객체에 끌어들인다. ID 참조가 이번 범위에 맞다.

### Validation

공통 식별자 규칙 `^[a-z0-9]+(?:-[a-z0-9]+)*$`를 `id`, `slug`, `provider_id`, `service_id`에 적용한다. name은 공백을 뺀 뒤 빈 문자열이면 `ValueError`다. 오류 메시지에는 필드 이름이 들어간다.

모델이 검사하지 않는 것:

- Provider, Service가 실제로 존재하는지
- slug가 부모 범위에서 중복되는지
- id가 저장소 기준으로 전역 유일한지

이 검사는 이후 Repository 또는 Catalog 계층의 책임이다.

### Relationship

`Service.provider_id`가 Provider를 가리키고, `Plan.service_id`가 Service를 가리킨다. `id`를 `split`하거나 `f"{provider_id}-{slug}"`로 관계를 만들지 않는다. 읽을 수 있는 id 문자열은 허용하지만, 그 형식을 규칙으로 쓰지 않는다.

### Tests

- `uv run pytest` — 72 passed.
  - FREE-001 health 테스트 4개 통과.
  - Provider: 생성, 필드, 빈 description, 불변성, slots, keyword-only, equality/hash, 잘못된 id/slug, 빈 name.
  - Service: 같은 기본 검증과 잘못된 `provider_id`.
  - Plan: 같은 기본 검증과 잘못된 `service_id`.
  - Cloudflare / Pages / Free 객체가 `provider_id`, `service_id`로만 연결되는지 확인. 시드 데이터가 아니다.

### Future Considerations

- 번들형 Provider처럼 한 상품이 여러 Service에 걸치면 현재의 Service 하나 대 Plan 하나 관계를 다시 검토한다.
- 가격과 무료 여부는 실제 제공 조건을 조사한 뒤 별도 Task에서 설계한다.
- 타입 체커를 도입하면 `NewType`으로 id를 나눌지 그때 검토한다.

## FREE-004 — Repository Layer

### Goal

Provider, Service, Plan을 저장하고 ID로 조회하는 Repository Layer를 만든다. 저장소 기술과 무관한 계약과 그 계약을 만족하는 인메모리 구현을 둔다. PostgreSQL과 Supabase는 연결하지 않는다.

### Design

- `CatalogRepository`는 `typing.Protocol`이다. Domain이 infrastructure를 import하지 않는다.
- 메서드는 `add_*`, `get_*`, `list_*`만 있다. ID 타입은 `str`이다.
- `InMemoryCatalogRepository`는 프로세스 메모리의 dictionary에 객체를 저장한다. 내부 자료구조는 외부에 노출하지 않는다.
- Contract Test는 구현체를 생성 함수로 주입받는다. 현재는 인메모리 구현만 연결한다.

### Responsibility

- Domain은 객체 자신의 필드 형식만 검사한다. 부모 존재와 slug 중복은 검사하지 않는다.
- Repository는 저장 제약을 검사한다. ID 중복, 부모 범위의 slug 중복, `Service.provider_id`와 `Plan.service_id`가 가리키는 엔티티의 존재다.
- 조회는 예외를 던지지 않는다. `get_*`는 없으면 `None`, `list_*`는 없으면 `()`다.
- 저장 검사는 모두 통과한 뒤에만 상태를 바꾼다. 실패하면 기존 데이터는 그대로다.

### Decisions

- Provider, Service, Plan Repository를 나누지 않고 `CatalogRepository` 하나로 둔다. Service는 Provider가, Plan은 Service가 있어야 저장되므로 카탈로그가 하나의 일관성 경계다. 저장소를 나누면 관계 검사가 여러 객체에 흩어진다.
- Protocol을 쓴다. Domain은 저장 기술에 의존하지 않고, 구현과 테스트가 같은 메서드 집합을 따른다.
- 인메모리를 먼저 둔다. 이번 Task의 목적은 계약과 저장 규칙이지 데이터베이스 연결이 아니다.
- `list_*`는 `tuple`을 반환한다. 내부 dictionary의 실시간 뷰가 아니고, 빈 결과도 `None`이 아닌 `()`다.
- 목록은 `id` 오름차순이다. 삽입 순서나 dictionary 순서에 기대지 않으며, 이후 PostgreSQL의 정렬과 같은 결과를 맞추기 위해서다.
- `update`, `delete`, `upsert`는 넣지 않는다. 조회와 추가만 필요한 시점이고, 변경 연산은 별도 Task에서 설계한다.
- PostgreSQL과 Supabase는 연결하지 않는다. 실제 스키마와 드라이버를 지금 고정하지 않기 위해서다.
- Contract Test의 동일성 비교는 값 비교다. 이후 데이터베이스 구현이 객체를 다시 만들어도 같은 테스트를 통과할 수 있다.
- pytest `pythonpath`에 backend 루트를 추가했다. 공통 Contract Test 모듈을 `tests.persistence`로 import하기 위해서다.

### Future

- PostgreSQL 또는 Supabase 구현을 추가할 때 같은 Contract Test를 재사용한다.
- 데이터베이스에서는 primary key, foreign key, unique 제약이 ID 중복, 부모 참조, slug 범위를 담당한다.
- 그 구현도 `CatalogRepository` Protocol을 따른다.

### Tests

- `uv run pytest` — 96 passed.
  - FREE-001부터 FREE-003까지의 기존 테스트 72개 통과.
  - Catalog contract 테스트 24개 통과. 인메모리 구현에 연결했다.

## FREE-005 — Capability / Limit / Source Domain

### Goal

Recommendation Engine이 나중에 쓸 카탈로그 메타데이터를 Domain과 Repository에 추가한다. Capability, Limit, Source를 표현하고 저장·조회한다. 추천 계산, 실제 Provider 데이터, PostgreSQL은 만들지 않는다.

### Design

- Capability는 저장 엔티티가 아니다. `CapabilityKey`는 `StrEnum` 고정 어휘이고, Plan의 `capabilities: frozenset[CapabilityKey]`로만 붙는다.
- Limit은 Plan에 속한다. 별도 id는 없고 자연 키는 `(plan_id, metric, period)`다.
- metric 이름에 기준 단위를 포함한다. `value`는 그 단위의 정수다.
- `value is None`은 명시적 무제한이다. Limit 행이 없으면 모름이다. `0`은 그 사용량을 제공하지 않음이다.
- Source는 독립 엔티티다. Limit이 `source_id`로 Source를 참조하고, 여러 Limit이 하나의 Source를 공유할 수 있다.
- Capability와 Limit은 직접 연결하지 않는다. 추천 엔진이 capability 필터와 limit 제약을 따로 조합한다.

### Repository

- `CatalogRepository`에 Source의 add/get/list와 Limit의 add/list를 추가했다. `get_limit()`은 두지 않았다.
- Limit 저장 시 Plan과 Source가 있는지 확인하고, 자연 키가 중복되면 `DuplicateEntityError`를 낸다.
- Source URL은 문자열 그대로 비교한다. 같은 URL은 `DuplicateEntityError`다. 정규화하지 않는다.
- 저장 검사가 실패하면 Repository 상태는 바뀌지 않는다.
- Contract Test에 Source와 Limit 계약, 그리고 테스트용 Cloudflare Pages/R2 메타데이터 예시를 추가했다. 예시 수치는 실제 무료 한도가 아니다.

### Deferred

- `effective_from`, versioning, rate limit, `on_exceed`, scope
- 실제 Provider 데이터와 Seed Loader
- Recommendation Engine
- `units.py`. GB/MB 변환은 실제 시드 데이터가 필요한 시점에 검토한다.

### Why

이후 Recommendation Engine은 Capability로 후보 Plan을 거르고, Limit으로 자원 한도를 거르며, Source로 근거와 조사 시점을 설명한다.

### Tests

- `uv run pytest` — 159 passed.
  - 기존 96개 테스트 통과.
  - FREE-005에서 Plan capability, Limit, Source, Catalog contract 테스트를 추가했다.

## FREE-006 — Catalog Seed

### Goal

확정된 Domain 모델에 Cloudflare, Render, Supabase의 실제 카탈로그 데이터를 Infrastructure Seed로 넣을 수 있게 한다. Recommendation Engine은 구현하지 않는다.

### Design

- Provider마다 `CatalogBundle`을 둔다. 공통 `load_catalog()`가 `CatalogRepository`에만 의존한다.
- 적재 순서는 Source, Provider, Service, Plan, Limit이다.
- `UnmodeledFact`는 현재 Domain이 저장하지 못하는 공식 문서 사실을 Source와 함께 보존한다. Repository에는 넣지 않는다.
- 공식 문서를 Source로 연결한다. 확인일은 2026-09-30이다.
- 문서가 GB/MB로 적은 양은 `domain/units.py`의 10진 상수를 사용한다.

### Decisions

- Pricing Model은 FREE-007 초반 설계로 보류한다. 이번 Seed의 Plan은 모두 Free라서 가격 모델을 검증할 데이터가 없다.
- Limit과 Price는 다른 개념이다. Limit은 Plan에 포함된 사용량이다. Base price는 사용량과 무관한 고정 요금이고, overage rate는 포함량을 넘긴 사용량의 단가이며, on exceed는 한도를 넘겼을 때의 동작이다. R2의 무료 Storage 10 GB와 초과 과금을 하나의 가격 필드로 합치지 않는다.
- `Plan.slug == "free"`를 가격 판단에 쓰지 않는다.
- 의미가 다른 수치를 기존 Metric으로 바꾸지 않는다. Pages의 500 builds/month, 20분 build timeout, Render의 750 instance hours/month와 0.1 CPU, 512 MB RAM, Supabase의 MAU, Edge Function invocations, Realtime messages는 Limit으로 등록하지 않는다.
- Pages와 Render Web Service Free는 현재 Limit이 없다. 이는 누락이 아니라 unknown이다.
- R2와 Supabase에서는 현재 Metric으로 표현되는 Limit만 등록한다. R2 egress는 `bandwidth-bytes` / `month` / `None`이다. `0`이 아니다.
- Source는 공식 문서 단위로 공유한다. 같은 문서가 여러 Limit과 Fact를 뒷받침한다.
- 같은 Seed를 두 번 적재하면 `DuplicateEntityError`로 실패한다. skip과 upsert는 쓰지 않는다. FREE-004에서 upsert를 제외했고, 조용히 옛 값이 남으면 Seed 변경을 놓친다. PostgreSQL 동기화는 별도 설계다.
- Provider, Service, Plan, Capability, Limit, Source Domain과 CatalogRepository, InMemory 구현은 바꾸지 않았다. 추가한 Domain 파일은 단위 상수 `units.py`뿐이다.
- `UnmodeledFact`는 Infrastructure 전용이다.

### FREE-007 준비사항

1. Limit 행이 없을 때의 unknown 처리 정책.
2. `UnmodeledFact`를 입력으로 쓰는 Caveat 모델.
3. Base price, overage rate, on exceed를 구분하는 최소 Pricing Model.
4. 전체 Plan 조회. 이번 작업에서는 `list_all_plans()`를 추가하지 않았다.
5. ProjectRequirement와 LimitMetric의 대응 관계. 새 Metric은 Engine이 실제로 판정할 요구사항을 확인한 뒤에 설계한다.

### Tests

- `uv run pytest` — 178 passed.
  - 기존 159개 테스트 통과.
  - Catalog loader, integrity, snapshot, semantic guard, source, engine readiness 테스트를 추가했다.

## FREE-007 PR 1 — Catalog 선행 작업

### Goal

Recommendation Engine을 구현하기 전에 Catalog 조회, 가격, Caveat Port를 준비한다. 실제 판정 로직은 구현하지 않는다.

### Design

- `CatalogRepository.list_all_plans()`는 저장된 모든 Plan을 `plan.id` 오름차순으로 반환한다. 빈 저장소는 `()`이다.
- `ExceedBehavior`는 `charged`, `suspended`, `restricted`다. Metric별 초과 동작은 모델링하지 않는다.
- `PlanPricing`은 Plan의 월 기본요금(USD cents)과 초과 시 가능한 동작 집합, `source_id`를 가진다.
- `add_plan_pricing()`은 Plan 존재, Source 존재, Plan당 Pricing 중복 순서로 검증한다. `get_plan_pricing()`은 없으면 `None`이다.
- `Caveat`는 id가 없는 값 객체다. `CaveatCatalog`는 `list_caveats(plan_id)`만 제공한다.
- `SeedCaveatCatalog`는 FREE-006 `UnmodeledFact`를 Infrastructure에서 `Caveat`로 변환한다. Repository에는 저장하지 않는다.

### Decisions

- 가격을 저장할 수 있는 구조만 추가하고, 실제 Provider 가격 Seed는 넣지 않는다. 공식 문서 확인과 Seed는 FREE-008로 미룬다.
- Caveat는 Entity가 아니다. persistence 대상이 아니고, Recommendation 판정에 쓰지 않는다.
- `UnmodeledFact`는 Domain Recommendation Engine이 import하지 않는다. Infrastructure의 `SeedCaveatCatalog`가 `Caveat`로 변환한다.
- PlanPricing은 Plan당 최대 하나다. `source_id`는 필수다. 기본요금 `0`은 무료 기본요금이고, 행이 없으면 가격 미확인이다.
- `list_all_plans()`는 삽입 순서와 관계없이 id 오름차순이다.
- Caveat 순서는 Seed의 `unmodeled_facts` 순서를 유지한다. 별도 정렬 키는 없다.
- `monthly_base_fee_usd_cents`만 둔다. Overage rate는 이번 모델에 넣지 않는다.

### Out of Scope

- Recommendation Engine
- ProjectRequirement
- Need
- Evaluator
- RecommendationService
- Pricing Seed
- API
- LLM
- PostgreSQL

### Test

- `uv run pytest` — 231 passed.
  - 기존 178개 테스트 통과.
  - Pricing, Caveat, `list_all_plans`, PlanPricing contract, SeedCaveatCatalog 테스트를 추가했다.

## FREE-007 PR2-1 — ProjectRequirement / Need

### Goal

`ProjectRequirement`를 정의하고, Recommendation Engine이 사용할 Need로 변환하는 기반을 만든다. Plan 평가는 구현하지 않는다.

### Design

```text
ProjectRequirement
        ↓
derive_needs()
        ↓
DerivedNeeds
 ├─ CapabilityNeed
 ├─ QuantityNeed
 ├─ BudgetNeed
 └─ unevaluated_features
```

`ProjectRequirement`는 무엇이 필요한지만 표현한다. 이 Plan이 요구사항을 만족하는지는 이후 Evaluator의 책임이다.

### Decisions

- Feature와 CapabilityKey를 분리했다. Feature는 사용자 요구이고, CapabilityKey는 Catalog가 제공하는 능력이다.
- `ai-api`는 현재 Capability로 평가할 수 없어 `unevaluated_features`에 보존한다. `server-compute`나 `serverless-functions`로 바꾸지 않는다.
- Quantity는 기존 `LimitMetric`과 `LimitPeriod`를 사용한다. 새 Metric과 Period는 추가하지 않는다.
- `file_storage_bytes`는 `file-storage-bytes` / `none` / `file-uploads`다. `database_size_bytes`는 `database-size-bytes` / `none` / `database`다.
- bandwidth는 현재 Plan-level quantity로 취급한다. `bandwidth-bytes` / `month`이며 `applies_to`는 `None`이다. 특정 Feature에 묶지 않는다.
- Need는 Entity가 아니다. id가 없는 Value Object다.
- `bool`은 integer quantity로 허용하지 않는다.
- resource quantity의 `0`은 허용하지 않는다. `None`은 해당 QuantityNeed를 만들지 않는다.
- budget의 `0`은 무료만 허용한다는 의미이므로 허용한다. `None`이면 BudgetNeed를 만들지 않는다.
- 단위 변환은 이 단계에서 하지 않는다. 입력 정수를 그대로 `required`로 옮긴다.
- `derive_needs()`는 Repository와 Infrastructure에 의존하지 않는다. 결과는 Feature 정의 순서와 quantity 필드 순서로 고정한다.

### Out of Scope

- ReasonCode
- CheckOutcome
- PlanEvaluation
- RoleEvaluation
- RecommendationService
- API
- LLM
- DB
- pricing seed
- actual recommendation ranking

### Test

- `uv run pytest` — 289 passed.
  - 기존 231개 테스트 통과.
  - ProjectRequirement validation과 `derive_needs()` 테스트를 추가했다.

## FREE-007 PR2-2 — ReasonCode / Check

### Goal

Need를 deterministic한 Check 결과로 평가하는 기반을 만든다. 여러 Check를 PlanEvaluation으로 집계하지 않는다.

### Design

```text
CapabilityNeed
      ↓
Capability Check
      ↓
ReasonCode + CheckOutcome
QuantityNeed
      ↓
Limit Check
      ↓
ReasonCode + CheckOutcome
BudgetNeed
      ↓
Budget Check
      ↓
ReasonCode + CheckOutcome
```

### Decisions

- ReasonCode를 판단의 핵심 결과로 사용한다. `CheckResult`는 reason code만 저장하고, outcome은 그 코드에서 계산한다.
- Outcome은 `satisfied`, `violated`, `unknown` 세 가지다. `unknown`을 `violated`로 취급하지 않는다.
- Capability 미제공은 `violated`다. 이번 단계에서는 후보 제외를 하지 않는다.
- Limit 초과는 `violated`다. 필요한 양이 Limit 값 이하이면 `within-limit`이다. 같은 값도 만족이다.
- `Limit.value=None`은 unlimited이며 `satisfied`다. `0`으로 해석하지 않는다.
- Limit 행이 없으면 `limit-not-found` / `unknown`이다.
- 같은 Metric이 있지만 Period가 다르면 `limit-period-mismatch` / `unknown`이다. Period를 변환하지 않는다. 같은 Metric과 Period가 있으면 그 Limit을 우선한다.
- Budget은 `monthly_base_fee_usd_cents`만 사용한다. `ExceedBehavior`는 예산 판단에 쓰지 않는다.
- Pricing이 없으면 `pricing-not-found` / `unknown`이다. 가격이 없다는 이유만으로 `over-budget`이 아니다.
- Check는 Repository를 호출하지 않는다. 이미 전달된 Plan, Limit 목록, PlanPricing만 본다.

### Out of Scope

- PlanEvaluation
- RoleEvaluation
- RecommendationEvaluation
- RecommendationService
- ranking
- caveat composition
- API
- LLM
- DB

### Test

- `uv run pytest` — 322 passed.
  - 기존 289개 테스트 통과.
  - ReasonCode 매핑, Capability, Limit, Budget Check 테스트를 추가했다.

## FREE-007 PR2-3 — Plan / Role / Recommendation Evaluation

### Goal

개별 Check 결과를 Plan, Role, 전체 Recommendation 수준으로 집계한다. RecommendationService와 Provider 조합은 구현하지 않는다.

### Design

```text
DerivedNeeds
    ↓
Role Candidate Plans
    ↓
PlanEvaluation
    ↓
RoleEvaluation
    ↓
RecommendationEvaluation
```

### Decisions

- 하나의 Plan이 모든 Feature를 만족해야 하는 구조는 쓰지 않는다. Feature별 Capability Role로 나눠 평가한다.
- Role 식별자는 `Feature`다. 별도 Role Entity는 만들지 않는다.
- Capability가 없는 Plan은 해당 Role의 candidate가 아니다. `incompatible`로 넣지 않는다.
- Role별 Capability는 `DerivedNeeds`의 `CapabilityNeed`를 사용한다. Feature와 CapabilityKey 매핑 표를 복제하지 않는다.
- Role-specific Quantity는 `applies_to == role`일 때만 `quantity_checks`에 들어간다.
- `applies_to is None`인 Quantity는 `global_quantity_checks`다. 현재는 monthly bandwidth다.
- 다른 Role의 Quantity는 현재 Role 평가에서 제외한다.
- Budget은 Plan-level check다. Budget이 없으면 `budget_check`는 `None`이다.
- Status는 `violated > unknown > satisfied` 우선순위다. 결과는 `incompatible`, `unknown`, `compatible`이다.
- `compatible`은 명시된 조건에서 위반과 미확인이 없다는 뜻이다. 추천 1순위가 아니다.
- ranking, winner selection, score는 구현하지 않는다.
- `ai-api`는 Role을 만들지 않고 `unevaluated_features`에 남긴다.
- `evaluate()`는 Repository와 Infrastructure를 호출하지 않는다. Limit과 Pricing은 인자로 받는다.
- Role 순서는 Feature 정의 순서다. Plan 순서는 `plan.id`다.

### Out of Scope

- RecommendationService
- Provider/Service composition
- PlanDetail
- Caveat
- Source
- ranking
- score
- winner
- API
- LLM
- DB

### Test

- `uv run pytest` — 338 passed.
  - 기존 322개 테스트 통과.
  - Plan, Role, Recommendation 집계와 multi-role 후보 분리 테스트를 추가했다.

## FREE-007 PR3-1 — Recommendation Application Service

### Goal

Recommendation Engine의 평가 결과를 Application Layer의 `RecommendationService`와 연결한다. Service는 추천을 결정하지 않는다.

### Responsibility

```text
Domain Engine = 판단
Application Service = 수집/위임/조립
Repository = Catalog 조회
```

### Design Decisions

- `recommend()`는 `list_all_plans()`로 모든 Plan을 Engine에 전달한다. Application에서 Capability로 미리 거르지 않는다.
- 모든 Plan의 Limit을 조회하고, Limit이 없어도 빈 tuple을 넣는다.
- Pricing은 `get_plan_pricing()`으로 조회한다. `evaluate()`가 `Mapping[str, PlanPricing]`을 받으므로 `None`은 맵에 넣지 않는다.
- Requirement는 기존 `derive_needs()`로 바꾼 뒤 `evaluate()`에 그대로 전달한다. Feature와 Capability 매핑을 다시 만들지 않는다.
- Evaluation에 등장한 Plan만 Service와 Provider를 조회한다. 같은 `recommend()` 호출 안에서만 로컬 캐시를 쓴다.
- `compatible`, `unknown`, `incompatible`에 나온 Plan을 모두 `PlanDetail`에 포함한다. 같은 Plan은 한 번만 만들고 `plan.id` 오름차순으로 정렬한다.
- Engine의 `RecommendationEvaluation`을 필터링하거나 다시 만들지 않고 `RecommendationResult.evaluation`에 그대로 넣는다.
- Plan이 가리키는 Service나 Provider가 없으면 기존 `RelatedEntityNotFoundError`를 발생시킨다. Repository와 Engine 예외는 삼키지 않는다.
- Caveat와 Source는 PR3-2로 미룬다.
- ranking, score, winner는 구현하지 않는다.

### Verification

- `uv run pytest tests/application/test_recommendation_service.py` — 13 passed.
- `uv run pytest tests/integration/test_recommendation_service_with_seed.py` — 1 passed.
- `uv run pytest` — 352 passed.
  - 기존 338개 테스트 통과.

## FREE-007 PR3-2 — Caveat / Source

### Goal

`RecommendationResult`와 `PlanDetail`에 Caveat과 Source 근거를 연결한다. 이 정보는 이미 계산된 Evaluation을 설명하며, 판정을 바꾸지 않는다.

### Design

```text
Evaluation
    ↓
PlanDetail
    ├── Caveats
    └── Sources
```

### Important Decisions

1. Caveat은 Evaluation에 등장한 모든 Plan에 연결한다.
2. incompatible Plan도 Caveat을 연결한다.
3. Source는 실제 Evaluation 증거, Pricing, Caveat에서만 수집한다.
4. Plan에 등록된 모든 Limit Source를 가져오지 않는다.
5. ReasonCode를 Application에서 다시 해석하지 않는다. `LimitCheck.limit`과 `other_period_limits`가 있는지만 본다.
6. Evaluation 객체는 변경하지 않는다. Caveat 내용이 달라도 Evaluation은 같다.
7. Source는 id 기준으로 중복을 제거하고 `source.id` 오름차순으로 정렬한다.
8. Source 조회 캐시는 `recommend()` 호출 안의 지역 변수다.
9. 누락된 Source는 `RelatedEntityNotFoundError`다. 여러 개가 없으면 source id 오름차순의 첫 항목에서 실패한다.
10. `PlanDetail.caveats`와 `sources`는 기본값 없는 필수 필드다.

이번 작업은 Case B다. 기존 `CheckResult`는 reason code만 가지고 있었다. `LimitCheck`와 `BudgetCheck`를 추가해 판정에 사용한 `Limit`과 `PlanPricing`을 결과에 보존했다. `check_limit()`과 `check_budget()`의 판정 분기는 바꾸지 않았다.

### Verification

- `uv run pytest` — 363 passed.
  - 기존 352개 테스트 통과.





