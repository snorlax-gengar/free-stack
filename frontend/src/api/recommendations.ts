import { requestJson } from './client.ts'
import type { RecommendationRequest, RecommendationResponse } from './types.ts'

export function postRecommendation(
  request: RecommendationRequest,
  options?: { signal?: AbortSignal },
): Promise<RecommendationResponse> {
  return requestJson<RecommendationResponse>('/api/v1/recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal: options?.signal,
  })
}
