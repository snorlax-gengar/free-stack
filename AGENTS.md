# Agent Guide

FreeStack 저장소에서 작업하는 AI Agent는 아래 규칙을 따른다.

## 작업 범위

- 요청된 Task 범위 안에서만 변경한다.
- 이번 기반 작업에서 도메인 모델, 데이터베이스, 인증, 추천 엔진, 배포 설정을 미리 만들지 않는다.
- 미래 기능을 위한 빈 폴더나 placeholder class를 추가하지 않는다.
- 현재 동작에 필요 없는 dependency를 추가하지 않는다.

## 테스트

- 기존 테스트를 깨뜨리지 않는다.
- 구현 후 관련 테스트를 실행하고, 실행 결과를 확인한 뒤에 완료로 보고한다.
- Backend 테스트는 `backend`에서 `uv run pytest`를 사용한다.
- Frontend 테스트는 `frontend`에서 `npm test`를 사용한다.

## 문서

- 동작, 실행 방법, 환경변수, 결정 사항이 바뀌면 `docs/dev-log.md`에 기록한다.
- `.env`는 커밋하지 않는다. 환경변수 예시는 `.env.example`만 갱신한다.
- `VITE_` 환경변수에 secret을 넣지 않는다.

## 완료 보고

구현이 끝나면 변경 파일, 테스트 결과, Frontend와 Backend 통신 확인 결과, 범위 밖 항목을 요약한다.
