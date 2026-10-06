import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Footer } from './Footer.tsx'

describe('Footer', () => {
  it('renders copyright, author, contact email, and github repo link', () => {
    render(<Footer />)

    expect(screen.getByText(/snorlax-gengar/)).toBeTruthy()
    expect(screen.getByText('✉️ gengarileo@gmail.com')).toBeTruthy()
    expect(
      screen.getByRole('link', { name: /이메일 보내기/ }).getAttribute('href'),
    ).toBe('mailto:gengarileo@gmail.com')
    expect(
      screen.getByRole('link', { name: /GitHub 저장소/ }).getAttribute('href'),
    ).toBe('https://github.com/snorlax-gengar/free-stack')
    expect(screen.getByText(/본 사이트에서 제공하는 무료 티어 한도 및 요금 정책/)).toBeTruthy()
  })
})
