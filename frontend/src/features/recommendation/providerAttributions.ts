export type ProviderAttribution = {
  providerId: string
  name: string
  sourceUrl: string
  sourceName: string
  license: string
}

export const PROVIDER_ATTRIBUTIONS: readonly ProviderAttribution[] = [
  {
    providerId: 'cloudflare',
    name: 'Cloudflare',
    sourceUrl: 'https://www.cloudflare.com/brand-assets/',
    sourceName: 'Cloudflare Brand Assets',
    license: 'All rights reserved by Cloudflare, Inc.',
  },
  {
    providerId: 'supabase',
    name: 'Supabase',
    sourceUrl: 'https://supabase.com/brand-assets',
    sourceName: 'Supabase Brand Assets',
    license: 'All rights reserved by Supabase, Inc.',
  },
  {
    providerId: 'render',
    name: 'Render',
    sourceUrl: 'https://render.com',
    sourceName: 'Render Brand Assets',
    license: 'All rights reserved by Render Services, Inc.',
  },
] as const
