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

## FREE-008 PR1 — Composition Domain Models

### Goal

FREE-008 Composition을 시작한다. 이번 PR은 Stack과 Composition 결과의 Value Object와 불변식만 확정한다. `compose()`와 Application Service는 만들지 않는다.

### Design

Stack은 평가된 모든 Role에 compatible 또는 unknown Plan을 하나씩 배정한 완전한 조합이다. 같은 Plan이 여러 Role을 맡는 Assignment는 각각 보존하고, `Stack.plan_ids`에는 그 Plan을 한 번만 넣는다.

```text
RoleAssignment
    ↓
Stack
    ├── plan_ids
    ├── status
    └── sort_key
CompositionResult
    ├── compatible / unknown / incompatible
    └── blocked_roles
```

### Important Decisions

- compatible과 unknown만 RoleAssignment가 될 수 있다. Role 단위 incompatible은 배정하지 않는다.
- `no-candidates`는 그 Role의 세 그룹이 모두 빈 경우다. `all-incompatible`은 incompatible 후보만 있는 경우다. Capability가 없어 후보가 아닌 Plan은 `all-incompatible`에 넣지 않는다.
- Stack status는 Assignment를 satisfied 또는 unknown으로 바꾼 뒤, budget check가 있으면 그 outcome을 더한다. violated가 있으면 incompatible, 없고 unknown이 있으면 unknown, 모두 satisfied면 compatible이다.
- `sort_key`와 그룹 정렬은 출력 순서를 고정하기 위한 것이다. 추천 순위가 아니다.
- Stack budget의 금액 계산은 다음 PR에서 한다. 이번 타입은 이미 계산된 `StackBudgetCheck`가 금액, reason, Plan 집합과 맞는지 검증만 한다.
- ranking, winner, score, best stack은 범위 밖이다.

### Design Deviations

Claude 설계의 접근 경로와 실제 FREE-007 코드가 다르다. FREE-007은 수정하지 않았고, 이번 PR은 Evaluation을 읽지 않는다.

- `role.need.feature`는 없다. `RoleEvaluation.role`이 `Feature`다.
- `plan_evaluation.plan_id`는 없다. Plan id는 `plan.id`다.
- `budget_result`는 없다. 필드명은 `budget_check`이고, 가격 증거는 `BudgetCheck.pricing`이다.
- `evaluation.requirement`는 없다. `RecommendationEvaluation`은 `roles`와 `unevaluated_features`만 가진다.
- `aggregate_status()`는 없다. 같은 규칙은 `PlanEvaluation.status` 안에 있다. `Stack.status`가 그 순서를 로컬에서 다시 적용한다.
- 공개 이름 `REASON_OUTCOMES`는 없다. 맵은 `_OUTCOME_BY_REASON`이다. `StackBudgetCheck.outcome`은 `CheckResult.outcome`으로 같은 맵을 읽는다.
- Composition의 Feature 정렬은 Feature 문자열 값 기준이다. FREE-007 Role 순서는 enum 선언 순서다.

### Verification

- `uv run pytest` — 396 passed.
  - 기존 363개 테스트 통과.

## FREE-008 PR2 — Composition Composer

### Goal

`RecommendationEvaluation`의 Role별 compatible/unknown 후보로 Cartesian Product를 만들어 `CompositionResult`를 반환한다.

### Decisions

- compatible과 unknown만 후보다. incompatible은 후보에서 뺀다.
- 모든 Role이 후보를 가질 때만 완전 조합을 만든다.
- `max_combinations`를 넘으면 일부 Stack을 반환하지 않고 `too-many-combinations`다. `combination_count`에는 전체 조합 수를 넣는다.
- `max_combinations`는 필수 keyword-only이며 1 이상의 int다. bool, 0, 음수, 정수가 아닌 값은 거부한다. 이 검증은 `no-roles` 판단보다 먼저다.
- Role이 없으면 `no-roles`이고 `combination_count`는 0이다. 빈 곱의 1을 쓰지 않는다.
- Stack 상태는 PR1 `Stack.status`가 계산한다. Composer는 그 값으로 그룹을 나눈다.
- 같은 Plan이 여러 Role을 맡는 것을 허용한다. Role마다 status가 다르면 Assignment에 그대로 남긴다.
- PR2는 `budget_check`를 계산하지 않고 `None`을 넣는다. Stack budget은 PR3에서 계산한다.
- Role 순서는 Feature 문자열 값 오름차순이다. 후보 순서는 plan id 오름차순이고, 그룹은 `Stack.sort_key` 오름차순이다.
- `unevaluated_features`는 조합을 막지 않으며 결과로 그대로 전달한다.

### Out of Scope

- Ranking
- Winner
- Budget calculation
- Limit calculation
- Application
- API
- LLM
- Repository
- Infrastructure

### Verification

- `uv run pytest` — 417 passed.
  - 기존 396개 테스트 통과.

## FREE-008 PR3 — Stack Budget

### Goal

Composer가 만든 `CompositionResult`에 Stack 단위 예산을 별도 순수 Domain 단계로 적용한다.

Stack Budget은 조합 생성과 분리되어 있다. 비용은 Role 수가 아니라 Stack의 unique Plan base fee 합계다.

### Responsibility

```text
Composer = 후보의 Cartesian Product
Budget = unique Plan base fee와 월 예산 비교
Stack.status = assignment와 budget_check를 함께 집계
```

### Budget input

- `monthly_budget_usd_cents`는 0 이상의 int다. bool, 음수, 정수가 아닌 값은 거부한다.
- 0은 허용한다.
- 검증은 composed가 아닌 결과보다 먼저 한다.

### Pricing aggregation

- Pricing은 `PlanEvaluation.budget_check`가 `BudgetCheck`일 때 `pricing`에서 읽는다. `budget_result` 필드는 없다.
- compatible, unknown, incompatible을 모두 본다.
- `None`이거나 budget check가 없으면 mapping에서 뺀다.
- 같은 Plan의 Pricing이 서로 다르거나, 한쪽만 `None`이면 `ValueError`다.
- 둘 다 없으면 오류가 아니다.

### Unique Plan 비용 계산

- `plan_ids`는 중복을 제거한 뒤 정렬한다.
- Pricing이 있으면 priced, 없으면 unpriced다.
- `known_total_usd_cents`는 priced Plan의 `monthly_base_fee_usd_cents`만 합한다. 없는 가격을 0원으로 두지 않는다.
- Stack에 없는 Pricing은 비용에 넣지 않는다.
- mapping key와 `PlanPricing.plan_id`가 다르면 오류다.
- `ExceedBehavior`는 판정에 쓰지 않는다.

### Priority

```text
over-budget > pricing-not-found > within-budget
```

알려진 합계가 예산을 넘으면 unpriced Plan이 있어도 `over-budget`이다. 합계가 예산과 같으면 넘지 않는다.

### Non-composed

`no-roles`, `blocked`, `too-many-combinations`는 예산 계산을 하지 않고 같은 객체를 반환한다. `pricing_by_plan`을 읽지 않는다.

### Stack status 재분류

새 `budget_check`만 붙인 Stack을 만들고, 그룹은 `Stack.status`로 다시 나눈다. Budget 모듈은 상태 우선순위를 따로 계산하지 않는다. 각 그룹은 `sort_key` 오름차순이다.

`blocked_roles`, `combination_count`, `unevaluated_features`는 유지한다. 이미 `budget_check`가 있으면 다시 적용하지 않는다.

### Deterministic ordering

- 수집한 Pricing map의 key는 plan id 오름차순이다.
- priced와 unpriced id도 오름차순이다.
- 재분류된 그룹도 `sort_key` 오름차순이다.

### Out of scope

- Composer 수정
- PR1 모델 수정
- FREE-007 수정
- Application, Repository, Infrastructure
- Pricing Seed
- Limit 평가, ranking, winner, API, LLM, DB

### Next step

Pricing Seed와 Application에서 `collect_plan_pricing` / `apply_stack_budget`을 연결하는 작업은 다음 PR이다.

### Verification

- `uv run pytest` — 435 passed.
  - 기존 417개 테스트 통과.

## FREE-008 PR4 — Stack Composition Application

### Goal

FREE-007 Recommendation과 FREE-008 Composition을 Application에서 조율한다. 판단 로직을 새로 만들지 않는다.

> FREE-008 PR4는 Composition Domain의 판단 로직을 추가하는 작업이 아니라, FREE-007 Recommendation과 FREE-008 Composition을 Application 계층에서 조율하는 작업이다.

### Application 책임

`StackCompositionService.compose_stacks()`는 다음 순서만 실행한다.

```text
ProjectRequirement
    → RecommendationService.recommend()
    → compose()
    → 예산이 있으면 collect_plan_pricing() + apply_stack_budget()
    → StackCompositionResult
```

### RecommendationService 재사용 이유

Catalog 조회, Evaluation, PlanDetail, Caveat, Source, Pricing 조립은 이미 `RecommendationService`에 있다. `StackCompositionService`는 Repository를 받지 않고 그 서비스를 주입받는다.

### StackCompositionService 명명 이유

이 서비스는 최적 Stack이나 순위를 고르지 않는다. 가능한 Stack 조합을 구성한다. 이름에 Recommendation을 쓰지 않는다.

### max_combinations

생성자 인자이며 기본값이 없다. 1 이상의 int만 허용한다. 사용자 입력이 아니라 Application 정책이다. 잘못된 설정은 `compose()` 전에 거절한다.

### Composition 실행 흐름

Composer와 Budget의 상태 분기를 Application에서 다시 하지 않는다. `no-roles`, `blocked`, `too-many-combinations`도 예산이 있으면 Budget 단계에 그대로 넘긴다.

### 예산 입력

예산은 `ProjectRequirement.monthly_budget_usd_cents`에서만 읽는다. `RecommendationResult`에는 requirement가 없다. `None`이면 `collect_plan_pricing()`과 `apply_stack_budget()`을 호출하지 않는다.

### Stack ↔ PlanDetail

Plan 상세는 `RecommendationResult.plans`에만 둔다. Stack은 plan id만 가진다. `plan_detail()`과 `stack_plan_details()`가 그 목록을 조회한다. 같은 Plan은 같은 `PlanDetail`이다. `stack.plan_ids`는 중복이 없으므로 여러 Role에 배정된 Plan도 한 번만 반환한다.

### Repository

Stack 상세를 위해 Repository를 다시 조회하지 않는다.

### 예외

새 예외를 만들지 않고, 발생한 예외를 다른 타입으로 바꾸지 않는다. Stack이 Recommendation에 없는 Plan을 가리키면 `ValueError`다. 없는 plan id 조회는 `KeyError`다.

### Result invariant

- Stack의 plan id는 Recommendation의 PlanDetail에 있어야 한다.
- `unevaluated_features`는 Evaluation과 Composition이 같다.
- 예산이 없으면 composed Stack의 `budget_check`는 `None`이다.
- 예산이 있고 `budget_check`가 있으면 그 금액은 requirement와 같다.

### Frontend / API

결과 객체에 requirement, recommendation, composition을 함께 둔다. 이후 화면은 Stack의 plan id로 이미 조립된 PlanDetail을 조회하면 된다. API와 화면은 이번 작업에 없다.

### Out of scope

- FastAPI, Pydantic DTO, Frontend
- DB, Pricing Seed
- LLM, ranking, winner
- Repository, LimitMetric

### Next step

FREE-009 Frontend.

### Verification

- `uv run pytest` — 460 passed.
  - 기존 435개 테스트 통과.

## FREE-009 PR2 — API Schema와 Mapper

### Goal

FREE-009 PR1 Contract를 PR1.5에서 확인한 Domain/Application 모델에 맞춰 Schema와 Mapper로 구현한다. HTTP Router, Dependency, Exception Handler는 만들지 않는다.

```text
HTTP JSON → Request Schema → to_requirement() → ProjectRequirement
StackCompositionResult → to_response(result) → Response Schema → HTTP JSON
```

### API 패키지

```text
backend/src/freestack/api/
├── __init__.py
├── schemas.py
└── mappers.py
```

`dependencies.py`, `errors.py`, `routes/`는 이번 PR에 없다.

### Request

`RecommendationRequest`는 `extra="forbid"`다. `features`는 Domain `Feature` enum이다. 알 수 없는 값과 중복은 Schema에서 거절한다. `ProjectRequirement`가 `frozenset`이라 중복이 Domain에 들어가면 사라지기 때문이다.

수량과 예산은 strict int다. bool, float, 숫자 문자열은 거절한다. `None`은 허용한다. 양수, 0, feature와의 교차 조건은 Schema에 다시 두지 않는다. 빈 feature 목록과 음수 수량은 Schema를 통과하고 `ProjectRequirement`에서 실패한다.

`to_requirement(dto)`는 필드를 복사만 한다.

### Response

`to_response(result)`만 있다. requirement는 `result.requirement`에서 읽는다.

`features`와 `unevaluated_features`는 `frozenset`이라 요청 순서가 없다. 응답 목록은 `Feature` 선언 순서다. 이 순서는 Evaluation role 순서와 같고, 입력 순서가 아니다.

`plans`는 `detail.plan.id`를 key로 하는 map이다. 값은 `plan`, `service`, `provider`, `pricing`, `caveats`, `sources`다. 같은 Plan은 한 번만 넣는다. Caveat에는 id가 없고 `plan_id`, `statement`, `source_id`만 있다. Source는 `id`, `url`, `checked_at`, `notes`다. 같은 Source가 여러 Plan에 있으면 최상위 `sources` map에는 id당 하나만 둔다. Plan 안의 목록은 그 Plan의 tuple 순서를 유지한다.

Evaluation은 `capability_check`, `quantity_checks`, `global_quantity_checks`, `budget_check`를 그대로 둔다. `kind`와 `required`는 없다. Limit는 세 상태를 구분한다.

- `limit`가 `None`이면 limit 행이 없다.
- `limit.value`가 `None`이면 unlimited다.
- `limit.value`가 `0`이면 제공 한도가 0이다.

사용자 요구량은 requirement에만 있다.

Stack budget은 `StackBudgetCheck`의 `budget_usd_cents`, `priced_plan_ids`, `unpriced_plan_ids`, `known_total_usd_cents`, `reason`, `outcome`이다. `budget_check`가 `None`이면 응답도 `null`이다. `pricing-not-found`는 Domain reason을 복사한다. Mapper는 가격을 다시 합산하지 않는다.

Composition status는 `composed`, `blocked`, `too-many-combinations`, `no-roles`다. `all-incompatible`과 `no-candidates`는 `blocked_roles`의 `BlockReason`이다.

Stack에는 id가 없다. key는 assignment 순서의 `feature=plan_id`를 `;`로 잇는다. Frontend가 이 문자열을 해석하지 않는다. `assignments`는 feature 값 오름차순이고, `plan_ids`는 정렬된 고유 id다. Mapper는 둘을 다시 정렬하지 않는다. Evaluation role 순서도 결과 tuple 그대로다.

### Out of scope

- Router, FastAPI endpoint, Dependency, Exception Handler
- Domain, Application, Infrastructure, `StackCompositionService` 수정
- CORS, Frontend

### Next step

FREE-009 PR3 Router, Dependency, Exception Handler.

### Verification

- `uv run pytest` — 484 passed.
  - 기존 460개 테스트 통과. API Schema/Mapper 테스트 24개 추가.

## FREE-009 PR3 — Recommendation API

### Goal

PR2 Schema와 Mapper를 FastAPI endpoint에 연결한다. Domain, Application, Infrastructure, Response Schema, Mapper는 바꾸지 않는다.

```text
HTTP Request
  → RecommendationRequest
  → to_requirement()
  → StackCompositionService.compose_stacks()
  → to_response()
  → RecommendationResponse
```

### Endpoint

`POST /api/v1/recommendations`

`create_app()`가 router를 `/api/v1` 아래에 등록한다. `GET /health`는 기존 그대로다.

### Dependency

`get_stack_composition_service()`만 Catalog를 조립한다.

```text
InMemoryCatalogRepository
  → load_catalog(ALL_BUNDLES)
  → RecommendationService(catalog, SeedCaveatCatalog)
  → StackCompositionService(recommendations, max_combinations=10)
```

`max_combinations`는 요청 필드가 아니다. 코드에 기존 설정값이 없어서 Dependency의 `DEFAULT_MAX_COMBINATIONS = 10`을 쓴다. 10은 seed 조합을 막지 않는 기존 테스트 값이다. Router는 Repository와 `RecommendationService`를 만들지 않는다.

### Exception mapping

응답은 `{"error": {"code", "message"}}`만 사용한다. `details`는 없다.

| 상황 | HTTP | code |
|---|---|---|
| Pydantic request validation | 422 | `REQUEST_VALIDATION_FAILED` |
| `to_requirement()`의 `ValueError` | 422 | `INVALID_REQUIREMENT` |
| `compose_stacks()`의 `ValueError` | 500 | `INTERNAL_ERROR` |
| `RepositoryError` 계열 | 500 | `INTERNAL_ERROR` |

`INVALID_REQUIREMENT`의 message는 `str(exc)`다. 500 message는 `An internal error occurred.`다. traceback과 exception repr은 응답에 넣지 않는다.

`ValueError`는 한 곳에서 한꺼번에 잡지 않는다. `to_requirement()`와 `compose_stacks()`의 경계가 다르다. Catalog 예외는 `RelatedEntityNotFoundError`, `DuplicateEntityError`, `DuplicateSlugError`의 부모인 `RepositoryError`다. `CatalogIntegrityError`는 만들지 않았다.

`composed`, `blocked`, `no-roles`, `too-many-combinations`는 HTTP 200이다.

### Architecture

Schema와 Mapper는 FastAPI와 Infrastructure를 import하지 않는다. Infrastructure import는 `dependencies.py`에만 있다. 이 경계에 맞추려고 mapper 테스트의 검사 대상을 `schemas.py`와 `mappers.py`로 좁혔다.

### Verification

- `uv run pytest` — 496 passed.
  - 기존 484개 테스트 통과. API HTTP 테스트 12개 추가.
- `git diff --check` 통과.

## FREE-009 PR4 — HTTP API Contract

### Goal

`POST /api/v1/recommendations`가 HTTP와 OpenAPI에서 PR2/PR3 계약과 같게 동작하는지 검증한다. Domain, Application, Infrastructure는 바꾸지 않는다.

### Verification

실제 ASGI 호출과 `app.openapi()`로 확인했다.

- 성공 응답은 HTTP 200, `application/json`이다. 최상위 필드는 `requirement`, `roles`, `composition`, `unevaluated_features`, `plans`, `sources`다.
- `plans[plan_id].plan.id`는 map key와 같다. Plan 값은 `plan`, `service`, `provider`, `pricing`, `caveats`, `sources`다.
- Caveat는 `plan_id`, `statement`, `source_id`다. Source는 `id`, `url`, `checked_at`, `notes`다.
- 예산이 없으면 stack `budget_check`는 `null`이다. 예산이 0이면 seed는 `pricing-not-found`를 그대로 반환하고, pricing을 `0`으로 만들지 않는다.
- 같은 요청의 stack key는 두 번 호출해도 같다. 테스트는 key를 parsing하지 않는다.
- HTTP JSON은 `to_response()` 결과와 같다. assignment 순서와 `plan_ids` 순서는 그 결과에 있다.
- `composed`, `blocked`, `no-roles`, `too-many-combinations`는 HTTP 200이다.
- Pydantic 실패는 422 `REQUEST_VALIDATION_FAILED`다. `ProjectRequirement`의 `ValueError`는 422 `INVALID_REQUIREMENT`다.
- `compose_stacks()`의 `ValueError`와 `RepositoryError`는 500 `INTERNAL_ERROR`이고 message는 `An internal error occurred.`다. PR3 테스트가 이 경로를 유지한다.
- `GET /health`는 200 `{"status": "ok"}`다.
- `GET /openapi.json`과 `GET /docs`는 200이다. operation은 `POST /api/v1/recommendations`다.
- `GET /api/v1/recommendations`는 405다. `POST /recommendations`와 `POST /api/recommendations`는 404다.

Request schema는 `features`만 required다. 수량 필드는 integer 또는 null이고 `additionalProperties`는 false다. OpenAPI의 integer는 JSON Schema 표현이다. bool과 숫자 문자열 거부는 Pydantic strict validation이 담당하며 PR3 HTTP 테스트가 유지한다.

### Deviation

OpenAPI 422가 FastAPI 기본 `HTTPValidationError`(`detail` 배열)를 가리켰다. 실제 응답은 `{"error": {"code", "message"}}`다.

`POST /api/v1/recommendations`의 422와 500 문서 schema를 `ErrorResponse`로 맞췄다. 응답 본문 처리와 Domain/Application은 바꾸지 않았다.

405와 404는 추천 오류 코드가 아니다. FastAPI의 `detail` 응답을 새 코드로 바꾸지 않았다.

### Verification result

- `uv run pytest` — 501 passed.
  - 기존 496개 테스트 통과. HTTP contract 테스트 5개 추가.
- `git diff --check` 통과.

## FREE-011 Frontend API Contract Verification

### Goal

FREE-010 frontend design assumptions against the actual backend/API contract. 프론트엔드와 API는 수정하지 않았다. 저장소에 FREE-010 설계 문서는 없다. 가정은 이번 검증에서 제시된 항목이다.

### Verification Scope

- Requirement, Feature, `derive_needs()`
- Quantity와 Budget
- `domain/units.py`와 catalog seed
- Recommendation / Composition response
- Plan details, sources
- Error contract, OpenAPI
- ASGI로 받은 실제 JSON. fixture 파일은 추가하지 않았다.

### Results

Role은 `Feature`에서 만든다. `derive_needs()`가 Feature를 `CapabilityNeed`로 바꾸고, 그 feature가 `RoleEvaluation.role`이 된다. `database_size_bytes`는 Role을 만들지 않는다.

- `database` Feature는 있다. JSON 값은 `"database"`다.
- Database Role을 만드는 입력은 `features`에 `"database"`를 넣는 것이다. `database_size_bytes`는 그 feature가 있을 때만 양의 int로 붙일 수 있다.
- `features: ["database"]`만으로도 role `database`가 생긴다. 이 응답의 `quantity_checks`는 빈 배열이다.
- `database_size_bytes`만 있고 `database` feature가 없으면 `422 INVALID_REQUIREMENT`다. 메시지는 `invalid database_size_bytes: ... requires database`다.
- `file_storage_bytes`도 같다. `file-uploads`가 필요하다.

`backend-server`와 `backend-functions`는 동시에 선택할 수 있다. 상호 배타 validation은 없다. 둘은 서로 다른 role로 평가된다. 실제 응답 role은 `backend-server`, `backend-functions`이고, 조합 status는 `composed`다. checkbox인지 radio인지는 API가 정하지 않는다.

수량 필드 `null`은 그 수량 조건이 없다는 뜻이다. Feature role은 남을 수 있다. `0`과 음수는 schema를 통과하고 `ProjectRequirement`에서 `422 INVALID_REQUIREMENT`다. `0`은 “0바이트를 요구”가 아니다. bool은 `422 REQUEST_VALIDATION_FAILED`다.

`monthly_budget_usd_cents`의 `null`은 예산 검사가 없다는 뜻이고 stack `budget_check`는 `null`이다. `0`은 유효하다. `BudgetNeed`는 0을 free-only 상한으로 둔다. 현재 seed에는 pricing이 없어서 이 요청의 reason은 `pricing-not-found`다. `known_total_usd_cents`가 `0`이어도 확정 가격이 아니다. bool과 음수는 거절된다. 음수는 도메인에서 `INVALID_REQUIREMENT`, bool은 schema에서 `REQUEST_VALIDATION_FAILED`다.

단위 상수는 두 종류다. `KB`/`MB`/`GB`/`TB`는 10의 거듭제곱이다. `KIB`/`MIB`/`GIB`/`TIB`는 2의 거듭제곱이다. Seed는 `MB`와 `GB`만 쓴다.

- `500 MB` = `500 * 10**6` = 500000000
- `1 GB` = `10**9` = 1000000000
- `5 GB` = 5000000000
- `10 GB` = 10000000000

요청과 응답의 canonical 값은 byte 정수다. Frontend는 이 정수를 보내고, seed의 GB/MB와 맞추려면 10의 거듭제곱으로 나누면 된다.

Role JSON:

```text
roles[].role
roles[].compatible | unknown | incompatible
  plan_id, role, status
  capability_check
  quantity_checks[]
  global_quantity_checks[]
  budget_check
```

`checks`라는 단일 배열은 없다. `evidence` 필드도 없다. `reason_code`와 `outcome`은 check 안에 있다. Candidate 안의 pricing은 `budget_check.pricing`뿐이다. Candidate 안에 sources는 없다.

Status 문자열은 `compatible`, `unknown`, `incompatible`다. Check outcome은 `satisfied`, `violated`, `unknown`이다. 둘 다 `unknown`이라는 문자열을 쓰지만 서로 다른 값이다.

ReasonCode JSON 값은 `capability-provided`, `capability-not-provided`, `within-limit`, `unlimited`, `exceeds-limit`, `limit-not-found`, `limit-period-mismatch`, `within-budget`, `over-budget`, `pricing-not-found`다. OpenAPI enum과 같다.

Composition 필드는 `status`, `compatible`, `unknown`, `incompatible`, `blocked_roles`, `combination_count`, `unevaluated_features`다. Stack은 상태별 배열에 나뉜다. Stack 필드는 `key`, `assignments`, `plan_ids`, `status`, `budget_check`다. `features` 필드와 별도의 total price 필드는 없다.

`budget_check`가 있을 때의 필드는 `budget_usd_cents`, `priced_plan_ids`, `unpriced_plan_ids`, `known_total_usd_cents`, `reason`, `outcome`이다. 예산이 없으면 이 객체 자체가 `null`이다. Frontend가 plan pricing을 합산할 값은 현재 seed에 없다. pricing은 `null`이다.

`plans`의 key는 `plan.id`와 같다. 같은 plan은 응답에 한 번만 있다. `pricing`은 `null`일 수 있다. Caveat는 `plan_id`, `statement`, `source_id`다. Plan의 `sources`와 최상위 `sources`는 `id`, `url`, `checked_at`, `notes`다. 최상위 map은 plan source를 id 기준으로 한 번만 담는다. URL은 최상위 `sources[id]` 또는 plan `sources`에서 읽으면 된다. Caveat와 limit는 `source_id`만 가진다.

`unevaluated_features`는 capability가 없는 feature다. 현재 매핑에 없는 feature는 `ai-api`뿐이다. `features: ["ai-api"]` 응답은 최상위와 composition 모두 `["ai-api"]`다. 순서는 Feature 선언 순서다.

Business status는 모두 HTTP 200이다.

- `composed`: stack이 `compatible`/`unknown`/`incompatible` 안에 있다. role evaluation이 있다. 예산이 없으면 `budget_check`는 `null`이다.
- `blocked`: `blocked_roles`가 있고 stack 배열은 비어 있다. role evaluation은 남아 있다. 예: authentication, realtime, bandwidth `10000000000`이면 두 role 모두 `reason: "all-incompatible"`이다.
- `no-roles`: `roles`는 `[]`, composition status는 `no-roles`, `combination_count`는 0, stack은 없다. `ai-api`는 `unevaluated_features`에 있다.
- `too-many-combinations`: stack 배열은 비어 있고 `combination_count`는 있다. `max_combinations`는 응답에 없다. 요청 필드도 아니다. 운영 값은 Dependency의 10이고, 현재 seed의 2개 조합은 이 상태에 들어가지 않는다.

`blocked_roles`는 `feature`와 `reason`이다. reason은 `no-candidates` 또는 `all-incompatible`이다.

에러 본문은 `{"error": {"code", "message"}}`뿐이다. `loc`, `field`, `detail`은 없다.

- schema 실패: `422`, `REQUEST_VALIDATION_FAILED`, message `Request validation failed.`
- `ProjectRequirement` 실패: `422`, `INVALID_REQUIREMENT`, message는 `str(exc)`
- 내부 `ValueError`와 `RepositoryError`: `500`, `INTERNAL_ERROR`, message `An internal error occurred.`

OpenAPI `POST /api/v1/recommendations`의 request는 `features`만 required다. 나머지 네 정수는 integer 또는 null이고 `additionalProperties`는 false다. Feature enum은 코드의 9개 값과 같다. 200은 `RecommendationResponse`, 422와 500은 `ErrorResponse`다.

분류:

- PASS: Feature `database`와 role 생성 경로, 수량 null, 예산 null/0, byte 정수와 seed의 10진 GB/MB, role/candidate/reason/composition/plans/sources/unevaluated, business status, OpenAPI.
- MISMATCH: “`database` feature가 없다”, “수량 0은 0바이트 요구”, “candidate에 단일 checks/evidence/sources가 있다”, “422에 field path가 있다”, “stack에 항상 total price가 있다”. 이는 FREE-010 가정과 실제 계약의 차이다. 현재 API를 이번 작업에서 바꾸지 않는다.
- NEEDS DECISION: backend 두 feature의 입력 위젯, 예산이 없을 때 카드 가격을 보여줄지, `pricing-not-found`의 `known_total_usd_cents: 0`을 어떻게 문구로 보일지, `too-many-combinations` 문구에 서버 한도를 넣을지, JSON fixture 파일을 저장소에 둘지.

### Frontend Impact

요청은 `features` 배열이 본 요구사항이다. Database는 `"database"`를 넣고, 크기가 필요할 때만 양의 `database_size_bytes`를 더한다. `backend-server`와 `backend-functions`는 함께 보낼 수 있다.

화면은 `roles`, 상태별 stack 배열, `plans[plan_id]`, 최상위 `sources`를 그대로 읽으면 된다. stack `key`는 해석하지 않는다. 가격은 `budget_check`가 있을 때만 `known_total_usd_cents`와 `reason`을 함께 보여야 한다. `reason`이 `pricing-not-found`이면 합계가 확정된 것이 아니다. plan pricing을 다시 더하지 않는다.

422는 필드별 경로가 없으므로 폼 필드에 자동으로 연결할 수 없다. `INVALID_REQUIREMENT`는 message 문자열만 있다.

### Next Decision Items

- `backend-server`와 `backend-functions`를 checkbox로 둘지.
- 예산을 입력하지 않은 stack 카드에 가격을 둘지.
- `pricing-not-found`일 때 `known_total_usd_cents`를 금액으로 보일지.
- `too-many-combinations` 설명에 한도 숫자를 넣을지. 응답에는 그 숫자가 없다.
- 검증용 JSON fixture를 저장소에 추가할지.

### Test

- `uv run pytest` — 501 passed.
- `uv run pytest tests/api` — 41 passed.
- 백엔드 코드는 바꾸지 않았다. 기존 FREE-007 / FREE-008 테스트를 포함해 skip은 없다.

## FREE-012 Frontend API Foundation

### Goal

FREE-013 Requirement Form이 사용할 OpenAPI 타입, API client, error model, byte/money formatter를 만든다. 화면 UI와 Backend 계약은 바꾸지 않는다.

### Design

우선순위는 실제 FastAPI OpenAPI, FREE-011 검증, 그다음 구현이다. `postRecommendation()`은 요청 JSON을 고치지 않는다. `null`과 `0`을 그대로 보낸다. composition status가 `blocked`, `no-roles`, `too-many-combinations`여도 HTTP 200이면 resolve한다.

### OpenAPI Generation

`frontend/scripts/dump-openapi.mjs`가 `uv run python`을 `spawnSync`로 실행하고 `freestack.main.app.openapi()`를 `frontend/openapi.json`에 쓴다.

`npm run api:gen`은 `npx --yes openapi-typescript@7.13.0 --enum-values`로 `frontend/src/api/schema.gen.ts`를 만든다. `openapi-typescript`는 TypeScript 5 peer라 devDependency에 넣지 않는다. 생성 후 `package-lock.json`은 변하지 않았다.

`schema.gen.ts`는 생성 파일이다. 비즈니스 로직을 직접 쓰지 않는다. oxlint는 이 파일을 오류 없이 통과해서 `.oxlintrc.json`에 ignore를 추가하지 않았다.

### Type Strategy

`src/api/types.ts`는 generated schema의 alias만 둔다. `ErrorObject.code`는 string이라 `KnownErrorCode`는 알려진 세 코드의 별도 union이다. 실제 `ApiError.code`는 임의 string을 받는다.

`tsconfig.app.json`에 `strict`와 `noUncheckedIndexedAccess`를 켰다. 기존 화면 코드의 동작은 바꾸지 않았다.

### API Client

`requestJson<T>()`가 base URL의 끝 슬래시를 제거하고 path를 붙인다. 2xx JSON은 `T`로 반환한다. `fetch` reject는 `ApiError` `kind: "network"`다. `AbortError`는 그대로 다시 throw한다. non-2xx이면서 `{ error: { code, message } }`이면 `kind: "http"`다. JSON이 아니거나 그 구조가 아니면 `kind: "unexpected-response"`다.

`getHealth()`도 `requestJson()`을 사용한다. `VITE_API_BASE_URL`이 없으면 기존처럼 `Error`를 throw한다.

### Error Handling

`ApiError`는 `erasableSyntaxOnly`에 맞게 필드를 constructor 안에서 할당한다. enum과 parameter property는 쓰지 않는다. runtime response schema validation은 하지 않는다.

### Units

`src/lib/units.ts`의 `MB`는 `1_000_000`, `GB`는 `1_000_000_000`이다. `toBytes()`는 0, 음수, 소수, NaN, Infinity, unsafe integer를 `RangeError`로 거절한다. `formatBytes()`는 1 GB 이상이면 GB, 1 MB 이상이면 MB, 그 미만은 B다. 소수는 최대 2자리이고 trailing zero는 뺀다. 천 단위 구분을 쓴다. feature와 `null`의 의미는 검사하지 않는다.

### Money

`formatUsdCents()`와 `wholeUsdToCents()`는 음수와 비정수를 거절한다. `formatUsdCents(0)`은 `"$0"`이다. `pricing === null`, `pricing-not-found`, `known_total_usd_cents === 0`의 의미는 판단하지 않는다.

### Tests

- `npm test` — 32 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.

### Decisions

- `openapi-typescript` 7.13.0을 `npx`로 실행한다.
- generated schema를 작업 트리에 둔다.
- `strict`와 `noUncheckedIndexedAccess`를 켠다.
- byte는 SI decimal이다.
- money는 cents 기준이다.
- runtime response validation은 도입하지 않는다.
- label 파일은 실제 사용 task에서 만든다.
- Backend Contract Issue #1과 #2는 이번 task에서 수정하지 않는다.

### Known API Contract Issues

- Issue #1: 422 `REQUEST_VALIDATION_FAILED`의 message는 고정 문장이고 `loc`/`field`가 없다. 폼 필드에 자동으로 연결할 수 없다.
- Issue #2: 수량 `0`은 `INVALID_REQUIREMENT`다. 예산이 있을 때 `known_total_usd_cents`가 `0`이고 reason이 `pricing-not-found`이면 확정 가격이 아니다. formatter는 이 판단을 하지 않는다.

### Out of Scope

Requirement Form, Recommendation UI, routing, Backend API, pricing seed, label placeholder.

## FREE-013 Requirement Form

### Goal

사용자 입력을 Form State로 두고, `RecommendationRequest`로 바꾼 뒤 `postRecommendation()`까지 호출한다. 추천 결과를 해석하거나 화면에 그리지 않는다.

### Scope

단일 `App` 화면에 Requirement Form을 연결했다. Router, 상태관리 라이브러리, UI 라이브러리, `user-event`, `jest-dom`은 추가하지 않았다. Backend, API 계약, Recommendation Engine, Composition은 변경하지 않았다. 결과 화면, Stack, Role, Plan, Source, Caveat, ranking, sorting, filtering은 구현하지 않았다.

FREE-012는 별도 commit이 되어 있지 않다. HEAD는 `37437e5 fix: align recommendation api contract`이고, FREE-012 파일은 작업 트리에 그대로 있다. 그 파일을 되돌리지 않고 그 위에 폼을 올렸다.

### UX decisions

- Router는 아직 도입하지 않는다.
- 예산 입력은 FREE-013에 포함한다.
- `backend-server`와 `backend-functions`는 배타적이지 않다. 둘 다 checkbox다.
- Feature 표시 문구는 `src/labels/features.ts`에만 둔다. Feature 값의 순서는 `schema.gen.ts`의 `featureValues`다. Label 파일에 Feature 배열을 다시 만들지 않는다.
- 파일 저장 용량 preset은 데이터베이스와 같이 `100 MB`, `500 MB`, `1 GB`, `5 GB`다. 명세의 파일 용량 구간은 `...`로만 적혀 있었다.
- 성공 시에는 `추천 결과를 받았습니다.`만 보인다. 응답 JSON은 화면에 없다.
- 기존 health 상태는 유지한다.

### Form State / API DTO boundary

`useReducer`의 `RequirementFormValues`는 문자열 amount를 유지한다. `""`와 `"0"`, 입력 중인 `"1."`을 구분하기 위해서다. 숫자 변환은 `toRecommendationRequest()`에서만 한다. 이 함수는 순수 함수이고, 추천 판단, capability, budget 판단, limit 비교, compatibility, composition, ranking을 하지 않는다.

Feature를 해제해도 quantity 문자열은 남긴다. 다시 선택하면 그 값이 보인다. submit 때는 선택되지 않은 Feature의 quantity를 검증하지 않고 `null`로 보낸다. Feature를 자동으로 추가하지 않는다.

요청은 항상 다섯 필드다. `features`, `file_storage_bytes`, `database_size_bytes`, `monthly_bandwidth_bytes`, `monthly_budget_usd_cents`. 빈 문자열은 보내지 않는다. 값이 없으면 `null`이다. `features` 순서는 클릭 순서가 아니라 `featureValues` 선언 순서다.

byte 변환은 `toBytes()`, 예산 변환은 `wholeUsdToCents()`를 쓴다. 단위 변환을 새로 만들지 않았다.

### null vs 0 semantics

- 빈 문자열은 조건 없음이다. quantity와 budget 모두 `null`이다.
- budget `"0"`은 월 `$0` 상한이다. API에는 `0` cents다.
- quantity `"0"`은 오류다. `null`로 바꾸지 않는다.
- 숨겨진 quantity는 입력값이 있어도 `null`이고 오류가 아니다.

### quantity behavior

선택된 Feature에 연결된 quantity만 검증하고 전송한다. 대역폭은 Feature에 묶이지 않아서 항상 표시하고, 값이 있으면 변환한다.

`trim()` 후 `^[0-9]+$`만 정수로 본다. `"-1"`, `"1.5"`, `"abc"`, `"1e3"`은 `not-integer`다. `"0"`은 `not-positive`다. `toBytes()`가 거절하면 `too-large`다.

- `500 MB` → `500000000`
- `1 GB` → `1000000000`
- `10 GB` → `10000000000`

### budget behavior

정수 달러만 받는다. `$4.99`는 지원하지 않는다.

- `""` → `null`
- `"0"` → `0`
- `"5"` → `500`
- `"10"` → `1000`

예산의 형식 오류 문구는 수량 문구와 다르다. `0`이 유효하므로 `0 이상의 정수로 입력해 주세요.`를 쓴다.

### error handling

로컬 검증 코드는 `required-feature`, `not-integer`, `not-positive`, `too-large`다. 서버 `message`는 UI에 노출하지 않는다. 분기는 `ApiError.kind`와 `ApiError.code`만 사용한다. 422를 특정 필드에 연결하지 않는다.

- `INVALID_REQUIREMENT` → 선택한 기능과 입력값의 조합을 처리할 수 없습니다. 입력 내용을 확인해 주세요.
- `REQUEST_VALIDATION_FAILED` → 요청을 처리할 수 없습니다. 입력 내용을 확인한 뒤 다시 시도해 주세요.
- `INTERNAL_ERROR`와 그 외 5xx → 일시적인 서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
- `network` → 서버에 연결할 수 없습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.
- `unexpected-response`, 알 수 없는 code, 일반 `Error` → 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.

`AbortError`는 화면 오류가 아니다. hook이 `AbortController`를 소유하고, unmount 시 abort한다. submitting 중 추가 submit은 handler에서 무시한다. 버튼은 `disabled`가 아니라 `aria-disabled="true"`다.

### accessibility

`fieldset` / `legend` / `label` / `input` / `select` / `button`을 사용한다. 기능 그룹 legend는 `필요한 기능`이다. checkbox의 접근 가능한 이름은 기능 제목만이고, 설명은 `aria-describedby`다. 수량 input은 `type="text"`와 `inputMode="numeric"`이다. `type="number"`는 쓰지 않는다.

필드 오류는 `aria-invalid`와 `aria-describedby`다. 색만으로 구분하지 않도록 오류 앞에 `오류:`를 붙인다. 서버 오류는 `role="alert"`다. 진행과 성공은 `role="status"`다. 제출 버튼은 `aria-disabled`와 `aria-busy`다. 형식 오류가 있으면 첫 오류 입력으로 focus를 옮긴다. `html lang`은 `ko`다.

CSS Modules, mobile first, 본문 최대 너비 640px, 1열, 터치 대상 약 44px, input 글자 크기 16px, focus ring을 유지한다.

### test results

- `npm test` — 65 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.

### manual E2E result

- `static-frontend` + `database` + `500 MB`: Backend 응답을 받았고, 화면에는 `추천 결과를 받았습니다.`만 표시됐다.
- `ai-api`: HTTP 200, composition `no-roles`. 화면도 성공 상태다.
- Backend를 끈 뒤 제출: `서버에 연결할 수 없습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.` (`role="alert"`). 확인 후 Backend를 다시 켰다.
- 키보드: 컨트롤은 모두 네이티브 checkbox, text input, select, button이고 `tabIndex`는 0이다. 자동화 도구의 Tab/Space는 trusted event가 아니라서 브라우저 기본 동작(포커스 이동, checkbox 토글)을 일으키지 않았다. 마우스 클릭, preset, 제출은 확인했다.

### known limitations

- 추천 결과 UI는 다음 task다.
- Router는 없다.
- 예산은 정수 달러만 받는다.
- 422는 필드 경로가 없으므로 서버 오류를 입력칸에 붙이지 않는다.
- Backend business logic을 Frontend에 복제하지 않았다.
- Feature를 입력값에 맞춰 자동으로 추가하지 않는다.

### UI

첫 화면을 동작 확인용 폼에서 MVP 소개 화면으로 바꿨다. API 요청, reducer, validation, `null`/`0` 의미는 그대로다.

- Header에 서비스 이름과 `무료/저비용 사이드프로젝트 인프라 추천`을 둔다. health 문장은 헤더의 작은 상태 정보로 남긴다.
- 소개 문구는 `내 프로젝트에 필요한 기능을 선택하세요.`와 `조건을 입력하면 적합한 인프라 조합을 찾아드립니다.`다.
- 본문은 최대 720px이다. 섹션은 `1. 필요한 기능`, `2. 사용량 조건`, `월 예산 (USD)`다. 예산 legend 앞의 `3. `는 `aria-hidden`이라 입력의 accessible name은 `월 예산 (USD)`다.
- Feature는 카드다. 모바일은 1열, 640px 이상은 2열이다. checkbox는 native이고, 이름은 기능 제목만이다. 설명은 `aria-describedby`다.
- 파일 저장과 데이터베이스 수량은 기능 목록 안이 아니라 사용량 섹션에 표시한다. 선택 해제 시 값은 state에 남고, 다시 선택하면 보인다. 요청에는 여전히 선택된 Feature의 수량만 들어간다.
- CTA는 `무료 스택 추천받기`다. 진행 문구 `추천 받는 중…`과 성공 문구 `추천 결과를 받았습니다.`는 유지한다. 버튼은 `aria-disabled`만 쓰고 HTML `disabled`는 쓰지 않는다.
- 페이지 배경, 카드, 입력, preset, 오류, 상태 문구는 CSS Modules와 `App.css`로 맞춘다. 새 dependency는 없다.

확인:

- `npm test` — 65 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.
- 데스크톱 viewport 1920px에서 form 너비 688px, Feature grid `313px 313px`, horizontal overflow 없음.
- 390px viewport에서 Feature grid는 1열이고 horizontal overflow 없음.
- 빈 폼 제출, 500 MB, `ai-api`, Backend 종료, 키보드 Tab/Space는 이번 UI 확인에서 브라우저 클릭이 승인되지 않아 다시 누르지 못했다. 같은 동작은 단위 테스트와 직전 수동 확인에서 통과했다.

## FREE-014 PR1 Submit State Ownership

### Goal

Recommendation Result를 붙이기 위해 Submit State의 소유권을 App으로 옮긴다. 결과 화면은 만들지 않는다.

### Design

App이 `useRecommendationSubmit()`을 호출한다. RequirementForm은 hook을 호출하지 않고, 이미 있는 submit 상태에서 필요한 값만 props로 받는다.

```text
submitting
succeeded
error
onSubmit
```

응답 객체는 App이 가진 `SubmitState` 안에 남는다. `result`나 `recommendationResponse` 같은 별도 상태는 만들지 않았다. 성공 화면은 기존처럼 `추천 결과를 받았습니다.`만 보여 주고, 응답 JSON은 그리지 않는다.

### Responsibility

- App: submission state owner. health 표시와 RequirementForm 연결.
- RequirementForm: 요구사항 입력, 로컬 validation, submit UI.
- useRecommendationSubmit: API request lifecycle. Abort, submitting guard, error 상태의 동작은 그대로다.

### Out of Scope

- Recommendation Result UI
- Stack / Role rendering
- Plan Detail
- Source / Caveat
- Router

### Tests

- `npm test` — 70 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.

## FREE-014 PR2 Recommendation Result Model

### Goal

Recommendation Result UI를 만들기 전에, Backend response를 화면에 옮길 작은 label, selector, formatter와 테스트 fixture를 둔다. 결과 화면은 만들지 않는다.

### Implemented

- `frontend/src/api/types.ts`에 generated schema alias를 추가했다. 새 DTO는 만들지 않았다.
- `frontend/src/lib/assertNever.ts`
- `frontend/src/labels/recommendation.ts` — EvaluationStatus, CheckOutcome, ReasonCode, BlockReason, CompositionStatus, LimitMetric, LimitPeriod, ExceedBehavior, CapabilityKey label과 `labelOf`
- `frontend/src/features/recommendation/resultModel.ts` — `byStatus`, `planRows`, `stackTitle`, `evaluationChecks`, `formatLimit`, `describeStackBudget`, `formatBudgetLimit`, `formatCheckedAt`, `formatSourceLink`
- `frontend/src/features/recommendation/fixtures/recommendationResponses.ts` — fixture A–I. 테스트 전용이다.

### Decisions

- Frontend does not recompute recommendation decisions.
- Backend response is the source of truth.
- Result model consists of small selectors/formatters rather than a large ViewModel.
- Fixtures are test-only.
- enum 값 목록은 generated schema를 다시 선언하지 않고 `satisfies Record<...>`로 label만 매핑한다.
- 알 수 없는 runtime code는 `labelOf`가 원본 code를 반환한다. metric formatter의 빠진 분기는 `assertNever`다.
- `outcome`은 API 값을 그대로 쓴다. reason code로 outcome을 다시 판단하지 않는다.
- `value === null`인 Limit은 제한 없음이다. `0`은 0이다. Limit 객체가 없는 것과 unlimited를 같은 문자열로 만들지 않는다.
- `pricing-not-found`이거나 가격이 있는 plan이 없으면 `knownTotalText`는 `null`이다. `known_total_usd_cents === 0`을 확정 금액 `$0`으로 바꾸지 않는다.
- byte 표시는 `formatBytes`, 금액 표시는 `formatUsdCents`를 재사용한다.
- `checked_at`은 `YYYY-MM-DD`만 `2026년 9월 30일`로 바꾸고, 그 외 문자열은 그대로 둔다. `Date`로 해석하지 않는다.
- Fixture A, B, B2, C, D, F는 현재 seed의 API 응답이다. E, H, I는 synthetic이다. G는 seed 응답에 `limit-period-mismatch` check 하나를 추가했다. seed에는 그 요청의 period mismatch가 없다.

### Frontend Responsibility

Frontend는 Backend가 정한 status, outcome, reason, budget, stack을 설명하는 문자열과 조회 결과만 만든다. compatible 재판단, stack 재조합, 가격 합산, 한도 초과 재계산, ranking은 하지 않는다.

### Testing

- `npm test` — 106 passed.
- `npm run build` — 통과. production bundle에 `too-many-fixture`가 없다.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.
- `git diff --check` — 통과.

### Out of Scope

- Recommendation Result UI
- Plan Detail dialog
- CSS 변경
- App, RequirementForm, `useRecommendationSubmit`, API client
- Backend, OpenAPI, generated schema 생성 로직
- 새 npm dependency

## FREE-014 PR3-1-T1 stackGroups

### Goal

Composition의 Stack을 상태별로 묶는 selector를 추가한다. Result UI는 만들지 않는다.

### Implemented

`stackGroups(composition)`를 `resultModel.ts`에 추가했다. `evaluationStatusValues` 순서인 `compatible`, `unknown`, `incompatible`로 Composition의 세 배열을 읽고, 빈 배열은 그룹에서 뺀다. 그룹 안의 Stack은 원본 배열 순서와 원본 객체 reference를 유지한다. Stack을 정렬하거나 복제하지 않고, compatibility와 budget도 다시 계산하지 않는다.

### Decisions

- `byStatus()`를 generic selector로 바꾸지 않았다. role evaluation과 composition stack은 입력이 다르고, 기존 `byStatus` 테스트를 유지하기 위해서다.
- Composition은 flat `stacks` 배열이 아니다. status별 배열이 이미 나뉘어 있으므로 `stackGroups`는 그 배열을 선언 순서로 꺼내기만 한다.
- Fixture H와 I는 focused result-model unit test용이다. 전체 응답 상태가 서로 일관되지 않아서 UI fixture로 쓰지 않는다. fixture 데이터는 바꾸지 않았다.

### Testing

- `npm test` — 112 passed. `stackGroups` 테스트 6개를 포함해 기존 106개도 통과했다.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `git diff --check` — 통과. CRLF 경고만 있다.

## FREE-014 PR3-1-T2 Recommendation Result UI

### Goal

`stackGroups()`를 쓰는 Recommendation Result 화면을 컴포넌트로 만든다. App에는 연결하지 않는다.

### Implemented

- `RecommendationResult`는 `RecommendationResponse`를 받아 결과 영역, 요구사항 요약, composition status를 그린다. 제목 `추천 결과`는 mount 때 한 번 focus한다.
- `composed`이면 `CompositionResult`를 그린다. 그 외 status는 `compositionStatusLabels` 한 줄만 보여 준다.
- `CompositionResult`는 `composition`과 `plans`만 받는다. stack 목록은 `stackGroups()`, 제목은 `stackTitle()`, plan 행은 `planRows()`, 예산은 `describeStackBudget()`를 사용한다.
- 요구사항 예산은 `formatBudgetLimit()`, 수량은 값이 있을 때만 `formatBytes()`다. `knownTotalText`가 null이면 합계 문구를 그리지 않는다.
- `unevaluated_features`가 있으면 기능 이름만 안내한다.

### Decisions

- Plan 묶음과 budget 판단은 UI에서 다시 하지 않는다.
- Stack key는 `stack.key`다. 화면에서 `sort()`하지 않는다.
- App 연결은 T3로 남긴다. 이 컴포넌트는 아직 App에 나타나지 않는다.

### Testing

- `RecommendationResult.test.tsx`에서 fixture A, F, G, D, B, C, E를 props로 렌더한다.
- `npm test` — 120 passed.
- `npm run build` — 통과. App이 Result를 import하지 않아 production bundle 구성은 이전과 같다.
- `npm run lint` — 통과.
- `git diff --check` — 통과. CRLF 경고만 있다.

## FREE-014 PR3-1-T3 App Connection

### Goal

성공한 추천 요청의 response를 Recommendation Result 화면에 연결한다.

### Implemented

App은 `submission.state.status === 'success'`일 때만 `RecommendationResult`에 `submission.state.response`를 넘긴다. 별도 표시 상태는 만들지 않았다. App은 stack, plan, budget을 해석하지 않는다. Result는 Requirement Form 다음에 온다. 기존 성공 문구 `추천 결과를 받았습니다.`는 그대로 둔다.

### Decisions

- 표시 조건은 PR1 submit state machine을 따른다. response 존재 여부로 판단하지 않는다.
- success 분기에서 TypeScript narrowing으로 response를 전달한다. type assertion은 쓰지 않는다.
- 성공 문구와 결과 제목이 함께 보이는 정리는 PR3-4로 남긴다.
- Requirement Form, API client, backend는 수정하지 않는다.

### Testing

- App 성공 테스트는 fixture A를 반환하고 `추천 결과`와 `Supabase Platform`이 보이는지 확인한다.
- health, submitting, error 테스트는 유지한다.
- `npm test` — 120 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `git diff --check` — 통과. CRLF 경고만 있다.

## FREE-014 PR3-2 Role / Plan Result UI

### Goal

추천 결과 화면에 Stack의 Feature 배정 상태와 Role별 후보 평가를 추가한다. Result model selector를 재사용하고, UI에서 평가를 다시 계산하지 않는다.

### Implemented

- `planLabel(detail, planId)`와 `describeCheckDetail(check)`를 `resultModel.ts`에 추가했다. 기존 selector는 바꾸지 않았다.
- `StatusBadge`는 `evaluationStatusLabels` 텍스트와 `data-status`를 보여 준다.
- `CompositionResult`의 Stack 상태는 `StatusBadge`다. Plan 행은 `planLabel` 한 줄이고, `row.assignments` 순서대로 기능 이름과 배정 status를 보여 준다.
- `RoleEvaluations`는 `roles.length > 0`일 때 composition 다음에 렌더한다. 표시 조건은 `composition.status`가 아니다. 각 Role은 접힌 `<details>`이고, summary는 `byStatus()` 개수다. 후보 Plan과 check는 `planLabel`, `StatusBadge`, `evaluationChecks`, `describeCheckDetail`로 표시한다. `CheckScope` 문구는 이 컴포넌트 안에 둔다.
- Fixture J는 `{"features":["static-frontend","file-uploads"]}`의 실제 API 응답이다. composed이고 Stack 2개이며, Cloudflare Pages가 공유되고 file-uploads 배정 Plan이 Stack마다 다르다.

### Decisions

- Role 평가는 Stack 카드와 분리했다. Stack은 배정된 기능과 그 상태를 보여주고, Role 영역은 후보 Plan의 check를 보여 준다. 두 결과를 한 카드에서 섞지 않는다.
- 같은 Plan이 여러 Feature를 담당하면 하나의 Plan 행 안에 Feature별 status를 둔다. assignment 순서는 API 순서를 유지한다.
- `describeCheckDetail`은 한도와 요금을 문장으로 바꿀 뿐 outcome, reason, 한도, 가격을 다시 판단하지 않는다. `pricing === null`은 금액으로 만들지 않는다.
- `<details>`는 모두 접힌 상태다. 상태별 자동 펼침은 하지 않는다.
- 구성 영역은 `role="region"` `aria-label="구성"`이다. Role 그룹 제목과 같은 문구가 생겨도 구성 제목을 그 영역 안에서 찾는다.

### Deferred

- PR3-3: Plan Detail dialog, Sources, Caveats, source link
- PR3-4: responsive, a11y 전체 점검, 상태별 details 자동 펼침, blocked / no-roles / too-many 전용 UX, Form 성공 문구 정리

### Testing

- `npm test` — 128 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.
- `git diff --check` — 통과. CRLF 경고만 있다.

## FREE-014 PR3-3 Plan Detail / Sources / Caveats

### Goal

Stack Plan과 Role 후보 Plan에서 같은 Plan Detail dialog를 연다. Backend 계약은 바꾸지 않는다.

### Implemented

- `PlanDetailDialog`는 native `<dialog>`다. 마운트 때 이전 focus를 저장하고 `showModal()`을 호출한다. 언마운트 때 열려 있으면 `close()`하고, 이전 요소가 문서에 남아 있으면 focus를 되돌린다.
- `RecommendationResult`만 `openPlanId`를 가진다. PlanDetail 객체는 state에 넣지 않고 `response.plans`에서 찾는다. 값이 있을 때만 dialog를 렌더한다.
- Stack Plan row와 Role 후보 모두 `상세 보기` 버튼을 둔다. `detail`이 없으면 버튼은 없고 `plan_id` 표시는 유지한다.
- 가격은 `pricing === null`과 요금 `0`을 구분한다. null은 가격 정보 없음이다. `0`은 `월 기본 요금 $0`이다.
- Caveat와 Pricing의 `source_id`는 `sourceNumber()`로 배열 위치 번호가 된다. `[출처 n]`은 dialog 안 Source 항목으로 이동한다.
- Source 목록 제목은 `이 결과에 사용된 출처`다. 링크는 `formatSourceLink()`를 쓰고, 확인일은 `formatCheckedAt()`이다. 빈 notes는 그리지 않는다.
- Fixture K는 `{"features":["backend-server"]}`의 실제 API 응답이다. Render Web Service Free, Source 2개, Caveat 11개.
- `sourceNumber(sources, sourceId)`만 추가했다. 못 찾으면 `null`이다.

### Decisions

- Plan 단위 상세이므로 화면마다 카드를 늘리지 않고 dialog 하나를 쓴다. 같은 Plan은 `openPlanId` 하나라 dialog 인스턴스도 하나다.
- Source 번호는 배열 위치다. 순위가 아니다. Backend가 준 순서를 재정렬하거나 중복을 제거하지 않는다.
- StrictMode가 effect를 다시 실행할 때 cleanup의 `close()`가 사용자 dismiss로 전달되면 dialog가 바로 사라진다. cleanup에서 난 `close`는 부모 `onClose`를 호출하지 않는다. 닫기 버튼과 Esc의 `close` 이벤트는 `openPlanId`를 지운다.
- 배경 클릭으로 닫지 않는다. Esc는 dialog의 기본 `cancel` 동작을 쓴다.

### Testing

- `showModal`/`close` stub은 `PlanDetailDialog.test.tsx`와 dialog를 여는 `RecommendationResult.test.tsx`의 beforeEach에만 있다. 전역 setup은 없다.
- 닫기 버튼, native close 이벤트, StrictMode remount, unmount focus 복원을 확인했다.
- Fixture K caveat 11개의 첫 참조는 출처 2, 마지막 참조는 출처 1이다.
- `npm test` — 147 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.
- `git diff --check` — 통과. CRLF 경고만 있다.

## FREE-014 PR3-4-1 Dialog 안정화

### Goal

Plan Detail Dialog가 StrictMode에서 열리자마자 닫히지 않게 하고, 모바일에서 닫기 버튼이 남으며, 출처 인용이 URL hash를 바꾸지 않게 한다.

### Implemented

- cleanup의 `close()`는 `closedByCleanup`을 이벤트 처리 전까지 유지한다. `close()`가 `open`을 먼저 지우고, StrictMode가 dialog를 다시 연 뒤에 `close` 이벤트가 도착할 수 있어서 `dialog.open`으로는 사용자 닫기와 cleanup을 구분하지 않는다.
- 닫기 버튼과 Escape의 `close` 이벤트는 `onClose()`를 호출한다. cleanup에서 난 `close`는 호출하지 않는다.
- Dialog는 header와 스크롤되는 body로 나뉜다. 제목과 닫기 버튼은 body 스크롤 밖에 있고, 닫기 버튼은 내용 폭으로 늘어나지 않는다.
- `[출처 n]`은 기본 anchor 이동을 막고 해당 Source `<li>`로 focus를 옮긴다. URL hash는 바꾸지 않는다.
- `showModal`/`close` stub은 `src/test/dialog.ts` 하나로 모았다. `close` 이벤트는 다음 microtask에서 발생한다.

### Testing

- StrictMode remount, unmount, 닫기 버튼, native close, source citation, 다시 열기를 테스트했다.
- `npm test` — 151 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과.
- `uv run pytest` — 501 passed.

## FREE-014 PR3-4-2 Abnormal Composition Status UX

### Goal

`blocked`, `too-many-combinations`, `no-roles`에서 조합이 만들어지지 않은 이유를 결과 화면에 설명한다. Backend와 API 계약은 바꾸지 않는다.

### Implemented

- `blocked`는 기존 상태 라벨 `조합 불가` 아래에, 막힌 역할과 `blockReasonLabels`(`후보 없음`, `모두 미충족`)를 목록으로 보여 준다. reason enum 문자열은 그대로 보이지 않는다.
- `too-many-combinations`는 `combination_count`를 `ko-KR` 천 단위로 설명한다. 0은 `0`으로 표시한다. 정수가 아니거나 음수면 개수 문장만 생략한다. 응답 타입의 `combination_count`는 `number`라서 `null`은 계약에 없다.
- `no-roles`는 기존 라벨 `평가할 역할 없음`과 함께, 선택한 기능 중 현재 평가하는 기능이 없다는 문장을 보여 준다.
- 최상위 `unevaluated_features`는 조합 상태 설명과 별도의 `평가하지 않은 기능` 목록이다. 어느 상태에서든 목록이 비어 있지 않으면 표시한다.
- `RoleEvaluations`에서 `blocked_roles`에 있는 역할만 `<details open>`으로 시작한다. 후보 그룹이 없는 역할은 빈 목록 대신 `사용 가능한 후보가 없습니다.`를 보여 준다.
- Fixture 파일은 바꾸지 않았다. `1,248`과 `0`, 그리고 blocked/too-many에 붙인 `ai-api`는 기존 fixture를 테스트에서 펼친 값이다. API에 없는 필드는 넣지 않았다.

### Testing

- `npm test` — 160 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과. `src/test/dialog.ts`의 `no-this-alias` warning은 PR3-4-1 stub에 있던 것이고 exit code는 0이다.
- `uv run pytest` — 501 passed.
- `git diff --check` — 통과. CRLF 경고만 있다.
- 브라우저에서 `blocked`와 `no-roles`를 조작하는 승인이 중간에 끊겨 375/768/1280 확인은 하지 못했다. 현재 seed의 최대 `combination_count`는 2이고 서버 한도는 10이라, 한도를 바꾸지 않으면 `too-many-combinations`는 라이브 응답으로 나오지 않는다.

## FREE-014 PR3-4-3 Result Structure / Presentation Cleanup

### Goal

추천 결과의 정보 구조와 간격을 정리한다. 추천 로직과 API는 바꾸지 않고, PR3-4-1 Dialog와 PR3-4-2 비정상 상태 설명은 유지한다.

### Implemented

- 요청 조건은 `h3`와 `기능` 라벨 아래의 기존 feature 목록, 수량 formatter, `formatBudgetLimit`으로 보여 준다.
- `h2 추천 결과` 아래에 `h3 조합`이 하나 있다. 상태 묶음 `충족 (1)`은 heading이 아니라 라벨이다. 개별 Stack은 `h4`다. `조합 불가`, `조합이 너무 많음`, `평가할 역할 없음`은 그 섹션 안의 `h4`다.
- RequirementForm의 `추천 결과를 받았습니다.`와 `succeeded` prop을 제거했다. 제출 중 `role="status"`와 오류 `role="alert"`는 남긴다.
- Status badge는 `inline-flex`, `width: fit-content`, `justify-self: start`라서 grid/flex 부모에서 내용 너비로 남는다.
- 결과 영역 heading, paragraph, list, details, summary의 기본 margin은 0이다. 간격은 기존 grid gap을 쓴다. 한글은 `word-break: keep-all`로 어절 경계에서 줄바꿈한다.
- summary는 최소 높이 44px이다. `display: flex`가 기본 disclosure marker를 지우므로, 같은 열림/닫힘 동작의 chevron을 붙였다.

### Testing

- `npm test` — 160 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과. `src/test/dialog.ts`의 `no-this-alias` warning은 기존 stub이고 exit code는 0이다.
- `uv run pytest` — 501 passed.
- `git diff --check` — 통과. CRLF 경고만 있다.
- 브라우저: 375에서 blocked와 no-roles, 375/768/1280에서 composed를 확인했다. badge는 46px이고 카드 전체 폭이 아니다. summary 높이는 44px이다. Dialog는 StrictMode 개발 서버에서 열리고, 닫으면 상세 보기 버튼으로 focus가 돌아온다. 출처 클릭은 URL hash를 바꾸지 않는다. `too-many-combinations`는 서버 한도 10과 현재 seed로는 라이브 응답이 되지 않는다.

## FREE-014 PR3-4-4 Role Evaluation Source Links

### Goal

역할 평가의 후보 검사에 출처가 있으면 `[출처 n]`을 보여 준다. 번호와 클릭 동작은 Plan Detail의 출처 목록과 같다. 새 dialog는 만들지 않는다.

### Implemented

- `checkSourceIds`가 quantity의 `limit.source_id`, `other_period_limits[].source_id`, budget의 `pricing.source_id`만 뽑는다. capability 검사는 빈 배열이다. 같은 id는 처음 순서를 유지한 채 한 번만 남긴다. `pricing`이 없으면 빈 배열이다.
- 번호는 해당 plan의 `sources` 배열 순서다. `sourceNumber`가 `null`이면 링크를 그리지 않는다. 응답에 plan detail이 없거나 source id를 찾지 못하면 검사 문장만 남는다.
- `[출처 n]`은 `SourceCitation` 하나다. Plan Detail의 가격·주의사항 인용과 역할 평가 인용이 같은 컴포넌트를 쓴다. 보이는 이름과 accessible name은 `[출처 n]`이다.
- 출처 `<li>` id는 `source-${planId}-${number}`다. 클릭은 기본 anchor 이동을 막고, 그 요소가 이미 DOM에 있으면 focus만 옮긴다. 없으면 기존 Plan Detail Dialog를 열고 해당 출처로 focus한다. URL hash는 바꾸지 않는다.
- Dialog mount effect의 dependency는 빈 배열이다. 열릴 때의 `detail`과 `focusSourceId`는 ref 초기값으로 읽고, `focusSourceId`를 dependency에 넣지 않는다. cleanup의 `closedByCleanup` 동작은 그대로다.
- 후보가 없는 역할의 `사용 가능한 후보가 없습니다.` 분기는 바꾸지 않았다. 검사 링크는 `white-space: nowrap`이다.
- Fixture 파일은 바꾸지 않았다. 출처가 둘인 경우와 없는 source id는 테스트에서 기존 fixture를 복제한 값이다. API에 없는 필드는 넣지 않았다.

### Testing

- `npm test` — 165 passed.
- `npm run build` — 통과.
- `npm run lint` — 통과. `src/test/dialog.ts`의 `no-this-alias` warning은 기존 stub이고 exit code는 0이다.
- `uv run pytest` — 501 passed. 이번 변경에 backend 파일은 없다.
- `git diff --check` — 통과. CRLF 경고만 있다.
- 브라우저: 정적 프론트엔드와 파일 업로드, 대역폭 10 GB 결과에서 역할 검사 `[출처 1]`이 보인다. 기능 충족 문장과 `한도 정보 없음`에는 링크가 없다. 375/768/1280에서 결과 폭은 688px이고 가로 overflow는 없다. 역할 인용을 클릭하면 Cloudflare · R2 · Free dialog가 열리고 출처 항목으로 focus가 가며 URL은 `http://127.0.0.1:5173/`이다. 닫으면 클릭한 `[출처 1]`로 focus가 돌아온다. Dialog 안의 출처 인용도 hash를 바꾸지 않는다. 후보 없음과 `blocked`/`no-roles`/`too-many-combinations`는 이번 브라우저 확인에서 다시 조작하지 않았다.
