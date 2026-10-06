import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ProviderIcon } from './ProviderIcon.tsx'
import { PROVIDER_ATTRIBUTIONS } from './providerAttributions.ts'

describe('ProviderIcon', () => {
  it('renders cloudflare icon correctly', () => {
    const { container } = render(<ProviderIcon providerId="cloudflare" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
    expect(svg?.getAttribute('aria-hidden')).toBe('true')
  })

  it('renders supabase icon correctly', () => {
    const { container } = render(<ProviderIcon providerId="supabase" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
  })

  it('renders render icon correctly', () => {
    const { container } = render(<ProviderIcon providerId="render" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
  })

  it('renders fallback icon when providerId is unknown', () => {
    const { container } = render(<ProviderIcon providerId="unknown-provider" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
  })

  it('contains all required provider attributions with valid URLs', () => {
    expect(PROVIDER_ATTRIBUTIONS.length).toBeGreaterThanOrEqual(3)
    const cloudflare = PROVIDER_ATTRIBUTIONS.find((p) => p.providerId === 'cloudflare')
    expect(cloudflare?.sourceUrl).toContain('cloudflare.com')

    const supabase = PROVIDER_ATTRIBUTIONS.find((p) => p.providerId === 'supabase')
    expect(supabase?.sourceUrl).toContain('supabase.com')

    const render = PROVIDER_ATTRIBUTIONS.find((p) => p.providerId === 'render')
    expect(render?.sourceUrl).toContain('render.com')
  })
})
