export type ProviderId = 'cloudflare' | 'supabase' | 'render' | (string & {})

export type ProviderIconProps = {
  providerId: string | null | undefined
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeMap = {
  sm: 16,
  md: 20,
  lg: 24,
}

export function ProviderIcon({ providerId, size = 'md', className }: ProviderIconProps) {
  const dimension = sizeMap[size]
  const normalizedId = providerId?.toLowerCase() ?? ''

  if (normalizedId.includes('cloudflare')) {
    return (
      <svg
        width={dimension}
        height={dimension}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
        role="img"
      >
        <path
          d="M18.995 10.999a4.802 4.802 0 0 0-4.646-3.606c-.45 0-.882.062-1.294.179A6.002 6.002 0 0 0 2.012 12.75a4.5 4.5 0 0 0 .988 8.75h15.995a5 5 0 0 0 .005-10.001z"
          fill="#F38020"
        />
        <path
          d="M17.4 16.5h1.6a2.8 2.8 0 0 0 .2-5.59 2.68 2.68 0 0 0-.7.09 2.8 2.8 0 0 0-5.38-1.13 3.36 3.36 0 0 0-.73-.09 3.36 3.36 0 0 0-3.26 2.6 2.52 2.52 0 0 0-.54-.06 2.52 2.52 0 0 0-2.52 2.52c0 .29.05.57.14.84h11.12a.84.84 0 0 0 .4-.78z"
          fill="#FAAE40"
        />
      </svg>
    )
  }

  if (normalizedId.includes('supabase')) {
    return (
      <svg
        width={dimension}
        height={dimension}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
        role="img"
      >
        <path
          d="M21.362 9.354H12V.396a.396.396 0 0 0-.716-.233L2.203 12.424l-.176.222H12v8.958a.396.396 0 0 0 .716.233l9.081-12.261.176-.222h-.611z"
          fill="#3ECF8E"
        />
      </svg>
    )
  }

  if (normalizedId.includes('render')) {
    return (
      <svg
        width={dimension}
        height={dimension}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
        role="img"
      >
        <path
          fillRule="evenodd"
          clipRule="evenodd"
          d="M12.247 18.064h-3.41v-3.793h3.41a1.896 1.896 0 1 0 0-3.793h-3.41V6.685h3.41a5.689 5.689 0 0 1 0 11.379zm-7.203 0H1.634V6.685h3.41v11.379zm14.406 0h-3.41V6.685h3.41v11.379z"
          fill="#0f172a"
        />
      </svg>
    )
  }

  // Fallback server/cloud icon
  return (
    <svg
      width={dimension}
      height={dimension}
      viewBox="0 0 24 24"
      fill="none"
      stroke="#64748b"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      role="img"
    >
      <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
      <line x1="6" y1="6" x2="6.01" y2="6" />
      <line x1="6" y1="18" x2="6.01" y2="18" />
    </svg>
  )
}
