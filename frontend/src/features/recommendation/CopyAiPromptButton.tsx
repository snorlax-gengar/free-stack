import { useState } from 'react'
import type { PlanDetail, Stack } from '../../api/types.ts'
import { buildAiPrompt } from './aiPrompt.ts'
import { copyToClipboard } from './clipboard.ts'
import styles from './RecommendationResult.module.css'

export type CopyAiPromptButtonProps = {
  stack: Stack
  plans: Readonly<Record<string, PlanDetail>>
}

export function CopyAiPromptButton({ stack, plans }: CopyAiPromptButtonProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    const promptText = buildAiPrompt(stack, plans)
    const success = await copyToClipboard(promptText)
    if (success) {
      setCopied(true)
      setTimeout(() => {
        setCopied(false)
      }, 2500)
    }
  }

  return (
    <div className={styles.copyPromptContainer}>
      <button
        type="button"
        className={`${styles.copyPromptButton} ${copied ? styles.copyPromptButtonSuccess : ''}`}
        onClick={handleCopy}
        aria-live="polite"
      >
        <span className={styles.copyPromptIcon} aria-hidden="true">
          {copied ? '✓' : '🤖'}
        </span>
        <span>{copied ? 'AI 개발 프롬프트가 복사되었습니다!' : 'AI 개발 프롬프트 복사 (Cursor / Claude)'}</span>
      </button>
      <p className={styles.copyPromptHint}>
        {copied
          ? '클립보드에 복사된 프롬프트를 Cursor나 Claude에 붙여넣어(Ctrl+V) 즉시 코딩을 시작하세요.'
          : '검증된 무료 스택과 제약사항을 포함한 프롬프트로 AI Agent에게 바로 개발을 지시하세요.'}
      </p>
    </div>
  )
}
