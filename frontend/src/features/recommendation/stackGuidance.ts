import type { PlanDetail, Stack } from '../../api/types.ts'

export type StackGuidance = {
  tags: readonly string[]
  description: string
}

export function getStackGuidance(
  stack: Stack,
  plans: Readonly<Record<string, PlanDetail>>,
): StackGuidance {
  const planDetails = stack.plan_ids
    .map((id) => plans[id])
    .filter((d): d is PlanDetail => d !== undefined)

  const serviceSlugs = new Set(planDetails.map((d) => d.service.slug))
  const providerSlugs = new Set(planDetails.map((d) => d.provider.slug))

  const tags: string[] = []

  // 태그 1: 비용 관련
  const isFree =
    (stack.budget_check !== null && stack.budget_check.known_total_usd_cents === 0) ||
    (planDetails.length > 0 &&
      planDetails.every(
        (d) => d.plan.id.endsWith('-free') || d.pricing?.monthly_base_fee_usd_cents === 0,
      ))
  if (isFree) {
    tags.push('💰 완전 무료 $0')
  }

  // 태그 2: 아키텍처 특성
  if (serviceSlugs.has('pages') || serviceSlugs.has('workers')) {
    tags.push('⚡ 서버리스/간편 배포')
  }
  if (serviceSlugs.has('web-service')) {
    tags.push('🖥️ 백엔드 서버형')
  }
  if (providerSlugs.has('supabase')) {
    tags.push('📦 올인원 BaaS')
  }
  if (serviceSlugs.has('r2')) {
    tags.push('📁 오브젝트 스토리지')
  }

  // 맞춤 가이드 설명 문구 (1위, 최적, Best 등의 단어 배제)
  let description = '선택하신 필요 기능을 효율적으로 제공하는 인프라 조합이에요.'

  if (serviceSlugs.has('pages') && providerSlugs.has('supabase') && serviceSlugs.has('web-service')) {
    description =
      '정적 웹 프론트엔드와 독립된 백엔드 API 서버(Node.js/Python), 데이터베이스를 모두 갖춘 풀스택 서비스에 잘 어울려요.'
  } else if (serviceSlugs.has('pages') && providerSlugs.has('supabase')) {
    description =
      'React나 Vue 기반 프론트엔드와 Supabase 백엔드로 시작하는 대중적인 조합이에요. 배포가 매우 쉽고 관리가 간편해요.'
  } else if (serviceSlugs.has('pages') && serviceSlugs.has('web-service')) {
    description =
      '정적 웹사이트와 상시 실행 백엔드 API 서버를 분리하여 운영하고 싶을 때 적합한 조합이에요.'
  } else if (serviceSlugs.has('pages') && serviceSlugs.has('r2')) {
    description =
      '웹사이트 호스팅과 함께 대용량 이미지·파일을 비용 부담 없이 안전하게 저장·제공할 때 유용한 조합이에요.'
  } else if (providerSlugs.has('supabase') && planDetails.length === 1) {
    description =
      '모바일 앱이나 별도 클라이언트의 백엔드 API, 데이터베이스, 사용자 인증을 한곳에서 해결하고 싶을 때 편리해요.'
  } else if (serviceSlugs.has('pages') && planDetails.length === 1) {
    description =
      '개인 포트폴리오, 블로그, 회사 소개 랜딩페이지를 비용 부담 없이 안정적으로 호스팅하기에 좋아요.'
  } else if (serviceSlugs.has('web-service') && planDetails.length === 1) {
    description =
      '직접 구현한 백엔드 웹 애플리케이션을 간편하게 클라우드 서버 환경에서 실행할 수 있어요.'
  }

  return {
    tags,
    description,
  }
}
