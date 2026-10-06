import './Footer.css'

export function Footer() {
  return (
    <footer className="footer" aria-label="사이트 푸터">
      <div className="footerDivider" />
      <div className="footerContent">
        <div className="footerMain">
          <p className="footerBrand">FreeStack</p>
          <p className="footerCopyright">
            © 2026 FreeStack. Designed & Built by <strong>snorlax-gengar</strong>.
          </p>
          <p className="footerDisclaimer">
            본 사이트에서 제공하는 무료 티어 한도 및 요금 정책은 각 서비스 공식 문서를 기반으로 수집·검증되었으나, 제공사의 사정에 따라 사전 고지 없이 변경될 수 있습니다.
          </p>
        </div>
        <div className="footerLinks">
          <div className="footerLinkGroup">
            <span className="footerLinkTitle">Contact & Feedback</span>
            <a
              href="mailto:gengarileo@gmail.com"
              className="footerLink"
              aria-label="제작자에게 이메일 보내기"
            >
              ✉️ gengarileo@gmail.com
            </a>
            <a
              href="https://github.com/snorlax-gengar/free-stack"
              target="_blank"
              rel="noopener noreferrer"
              className="footerLink"
              aria-label="FreeStack GitHub 저장소 (새 탭에서 열림)"
            >
              <svg
                className="githubIcon"
                viewBox="0 0 24 24"
                width="14"
                height="14"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z" />
              </svg>
              GitHub 저장소
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
