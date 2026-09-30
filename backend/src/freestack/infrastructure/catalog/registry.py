from freestack.infrastructure.catalog.bundle import CatalogBundle
from freestack.infrastructure.catalog.cloudflare import CLOUDFLARE
from freestack.infrastructure.catalog.render import RENDER
from freestack.infrastructure.catalog.supabase import SUPABASE

ALL_BUNDLES: tuple[CatalogBundle, ...] = (
    CLOUDFLARE,
    RENDER,
    SUPABASE,
)
