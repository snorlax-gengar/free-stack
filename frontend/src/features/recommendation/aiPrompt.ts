import type { PlanDetail, Stack } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { stackTitle } from './resultModel.ts'

export function buildAiPrompt(stack: Stack, plans: Readonly<Record<string, PlanDetail>>): string {
  const title = stackTitle(stack, plans)

  // 1. Service list with assigned roles and plan names
  const services = stack.plan_ids.map((id) => {
    const detail = plans[id]
    if (!detail) {
      return `- ${id}`
    }
    const assignedRoles = stack.assignments
      .filter((a) => a.plan_id === id)
      .map((a) => featureLabels[a.feature] ?? a.feature)
      .join(', ')
    const roleTag = assignedRoles ? `[${assignedRoles}] ` : ''
    return `- ${roleTag}${detail.provider.name} ${detail.service.name} (${detail.plan.name} 플랜)`
  })

  // 2. Caveats per plan
  const caveatsList: string[] = []
  for (const id of stack.plan_ids) {
    const detail = plans[id]
    if (!detail || detail.caveats.length === 0) {
      continue
    }
    const providerServiceName = `${detail.provider.name} ${detail.service.name}`
    for (const caveat of detail.caveats) {
      caveatsList.push(`- [${providerServiceName}] ${caveat.statement}`)
    }
  }

  const promptSections = [
    `# FreeStack 추천 무료 기술 스택 기반 프로젝트 개발 프롬프트`,
    ``,
    `## 1. 선택된 무료 기술 스택 조합: ${title}`,
    ...services,
    ``,
  ]

  if (caveatsList.length > 0) {
    promptSections.push(
      `## 2. 준수해야 할 무료 티어 핵심 제약사항 (과금 방지 필수 준수)`,
      `FreeStack 카탈로그에서 검증된 공식 무료 제약사항입니다. 이 한도를 초과하지 않도록 설계해주세요:`,
      ...caveatsList,
      ``,
    )
  }

  promptSections.push(
    `## 3. AI Agent (Cursor / Claude / ChatGPT) 지침 및 요청 사항`,
    `위의 무료 스택과 서비스별 제약사항을 만족하는 초기 웹 애플리케이션 프로젝트를 구축하려고 합니다.`,
    `아래 항목에 맞추어 실제 동작 가능한 프로젝트 설정과 코드를 작성해주세요:`,
    ``,
    `1. **프로젝트 초기화 및 권장 디렉토리 구조**:`,
    `   - 최신 모던 프레임워크(예: Next.js App Router 또는 Vite React) 기반 초기화 명령어`,
    `   - 추천 폴더 트리 구조 및 필수 패키지 설치 명령어`,
    `2. **환경 변수 구성 (.env.example)**:`,
    `   - 위 서비스들을 연동하기 위한 필수 환경 변수 템플릿 및 설정 안내`,
    `3. **클라이언트 SDK 연동 및 최소 동작 예제**:`,
    `   - 안전한 클라이언트 초기화 코드`,
    `   - 프론트엔드와 백엔드/DB 간의 기본 연동을 검증할 수 있는 샘플 코드`,
    `4. **무료 한도 준수 및 운영 팁**:`,
    `   - 상기 명시된 무료 용량/호출 제한을 초과하여 요금이 발생하지 않도록 방어하는 개발 모범 사례(커넥션 풀링, 캐싱, 정적 에셋 최적화 등)`,
  )

  return promptSections.join('\n')
}
