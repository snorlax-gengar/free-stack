import type { Feature } from '../api/types.ts'

export const featureLabels = {
  'static-frontend': '정적 프론트엔드',
  'backend-server': '백엔드 서버',
  'backend-functions': '서버리스 함수',
  database: '데이터베이스',
  'file-uploads': '파일 업로드',
  authentication: '인증',
  realtime: '실시간',
  'scheduled-jobs': '예약 작업',
  'ai-api': 'AI API',
} satisfies Record<Feature, string>

export const featureDescriptions = {
  'static-frontend': '빌드된 HTML·CSS·JS를 호스팅',
  'backend-server': '항상 실행되는 API 서버',
  'backend-functions': '요청이 올 때 실행되는 함수',
  database: '데이터를 저장하고 조회',
  'file-uploads': '사용자가 올린 파일을 저장',
  authentication: '회원가입과 로그인',
  realtime: '실시간 업데이트와 구독',
  'scheduled-jobs': '정해진 시간에 실행되는 작업',
  'ai-api': 'AI 모델 호출',
} satisfies Record<Feature, string>
