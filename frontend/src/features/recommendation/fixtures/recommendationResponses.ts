import type { RecommendationResponse } from '../../../api/types.ts'

// Test-only Recommendation API responses. Production code must not import this module.
// H/I are retained for focused result-model unit tests and are not used
// as complete UI-rendering fixtures because their full response state is
// not internally consistent.

export const fixtureA = {
  "requirement": {
    "features": [
      "database",
      "authentication",
      "realtime"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "database",
      "compatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "database",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    },
    {
      "role": "authentication",
      "compatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "authentication",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    },
    {
      "role": "realtime",
      "compatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "realtime",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [
      {
        "key": "authentication=supabase-platform-free;database=supabase-platform-free;realtime=supabase-platform-free",
        "assignments": [
          {
            "feature": "authentication",
            "plan_id": "supabase-platform-free",
            "status": "compatible"
          },
          {
            "feature": "database",
            "plan_id": "supabase-platform-free",
            "status": "compatible"
          },
          {
            "feature": "realtime",
            "plan_id": "supabase-platform-free",
            "status": "compatible"
          }
        ],
        "plan_ids": [
          "supabase-platform-free"
        ],
        "status": "compatible",
        "budget_check": null
      }
    ],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 1,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "Official Supabase billing documentation."
    }
  }
} satisfies RecommendationResponse

export const fixtureB = {
  "requirement": {
    "features": [
      "static-frontend",
      "scheduled-jobs"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [
        {
          "plan_id": "cloudflare-pages-free",
          "role": "static-frontend",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    },
    {
      "role": "scheduled-jobs",
      "compatible": [],
      "unknown": [],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "blocked",
    "compatible": [],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [
      {
        "feature": "scheduled-jobs",
        "reason": "no-candidates"
      }
    ],
    "combination_count": 0,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "cloudflare-pages-free": {
      "plan": {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare Pages plan.",
        "capabilities": [
          "static-hosting"
        ]
      },
      "service": {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "Static site hosting."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan includes 500 builds per month.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan allows one build at a time.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Builds time out after 20 minutes.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A Free plan site can contain up to 20,000 files.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A single Pages asset can be at most 25 MiB.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Requests to Pages Functions count toward the Workers plan quota.",
          "source_id": "cloudflare-pages-limits"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-pages-limits",
          "url": "https://developers.cloudflare.com/pages/platform/limits/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare Pages limits."
        }
      ]
    }
  },
  "sources": {
    "cloudflare-pages-limits": {
      "id": "cloudflare-pages-limits",
      "url": "https://developers.cloudflare.com/pages/platform/limits/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare Pages limits."
    }
  }
} satisfies RecommendationResponse

export const fixtureB2 = {
  "requirement": {
    "features": [
      "authentication",
      "realtime"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": 10000000000,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "authentication",
      "compatible": [],
      "unknown": [],
      "incompatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "authentication",
          "status": "incompatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [
            {
              "reason_code": "exceeds-limit",
              "outcome": "violated",
              "limit": {
                "plan_id": "supabase-platform-free",
                "metric": "bandwidth-bytes",
                "period": "month",
                "value": 5000000000,
                "source_id": "supabase-billing"
              },
              "other_period_limits": []
            }
          ],
          "budget_check": null
        }
      ]
    },
    {
      "role": "realtime",
      "compatible": [],
      "unknown": [],
      "incompatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "realtime",
          "status": "incompatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [
            {
              "reason_code": "exceeds-limit",
              "outcome": "violated",
              "limit": {
                "plan_id": "supabase-platform-free",
                "metric": "bandwidth-bytes",
                "period": "month",
                "value": 5000000000,
                "source_id": "supabase-billing"
              },
              "other_period_limits": []
            }
          ],
          "budget_check": null
        }
      ]
    }
  ],
  "composition": {
    "status": "blocked",
    "compatible": [],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [
      {
        "feature": "authentication",
        "reason": "all-incompatible"
      },
      {
        "feature": "realtime",
        "reason": "all-incompatible"
      }
    ],
    "combination_count": 0,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "Official Supabase billing documentation."
    }
  }
} satisfies RecommendationResponse

export const fixtureC = {
  "requirement": {
    "features": [
      "ai-api"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [],
  "composition": {
    "status": "no-roles",
    "compatible": [],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 0,
    "unevaluated_features": [
      "ai-api"
    ]
  },
  "unevaluated_features": [
    "ai-api"
  ],
  "plans": {},
  "sources": {}
} satisfies RecommendationResponse

export const fixtureD = {
  "requirement": {
    "features": [
      "static-frontend",
      "ai-api"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [
        {
          "plan_id": "cloudflare-pages-free",
          "role": "static-frontend",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [
      {
        "key": "static-frontend=cloudflare-pages-free",
        "assignments": [
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "compatible"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free"
        ],
        "status": "compatible",
        "budget_check": null
      }
    ],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 1,
    "unevaluated_features": [
      "ai-api"
    ]
  },
  "unevaluated_features": [
    "ai-api"
  ],
  "plans": {
    "cloudflare-pages-free": {
      "plan": {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare Pages plan.",
        "capabilities": [
          "static-hosting"
        ]
      },
      "service": {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "Static site hosting."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan includes 500 builds per month.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan allows one build at a time.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Builds time out after 20 minutes.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A Free plan site can contain up to 20,000 files.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A single Pages asset can be at most 25 MiB.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Requests to Pages Functions count toward the Workers plan quota.",
          "source_id": "cloudflare-pages-limits"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-pages-limits",
          "url": "https://developers.cloudflare.com/pages/platform/limits/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare Pages limits."
        }
      ]
    }
  },
  "sources": {
    "cloudflare-pages-limits": {
      "id": "cloudflare-pages-limits",
      "url": "https://developers.cloudflare.com/pages/platform/limits/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare Pages limits."
    }
  }
} satisfies RecommendationResponse

export const fixtureE = {
  "requirement": {
    "features": [
      "database",
      "authentication",
      "realtime"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "database",
      "compatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "database",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    },
    {
      "role": "authentication",
      "compatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "authentication",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    },
    {
      "role": "realtime",
      "compatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "realtime",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "too-many-combinations",
    "compatible": [],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 12,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "too-many-fixture"
    }
  }
} satisfies RecommendationResponse

export const fixtureF = {
  "requirement": {
    "features": [
      "static-frontend",
      "database"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": 0
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [],
      "unknown": [
        {
          "plan_id": "cloudflare-pages-free",
          "role": "static-frontend",
          "status": "unknown",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": {
            "reason_code": "pricing-not-found",
            "outcome": "unknown",
            "pricing": null
          }
        }
      ],
      "incompatible": []
    },
    {
      "role": "database",
      "compatible": [],
      "unknown": [
        {
          "plan_id": "supabase-platform-free",
          "role": "database",
          "status": "unknown",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": {
            "reason_code": "pricing-not-found",
            "outcome": "unknown",
            "pricing": null
          }
        }
      ],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [],
    "unknown": [
      {
        "key": "database=supabase-platform-free;static-frontend=cloudflare-pages-free",
        "assignments": [
          {
            "feature": "database",
            "plan_id": "supabase-platform-free",
            "status": "unknown"
          },
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "unknown"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free",
          "supabase-platform-free"
        ],
        "status": "unknown",
        "budget_check": {
          "budget_usd_cents": 0,
          "priced_plan_ids": [],
          "unpriced_plan_ids": [
            "cloudflare-pages-free",
            "supabase-platform-free"
          ],
          "known_total_usd_cents": 0,
          "reason": "pricing-not-found",
          "outcome": "unknown"
        }
      }
    ],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 1,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "cloudflare-pages-free": {
      "plan": {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare Pages plan.",
        "capabilities": [
          "static-hosting"
        ]
      },
      "service": {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "Static site hosting."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan includes 500 builds per month.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan allows one build at a time.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Builds time out after 20 minutes.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A Free plan site can contain up to 20,000 files.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A single Pages asset can be at most 25 MiB.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Requests to Pages Functions count toward the Workers plan quota.",
          "source_id": "cloudflare-pages-limits"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-pages-limits",
          "url": "https://developers.cloudflare.com/pages/platform/limits/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare Pages limits."
        }
      ]
    },
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "cloudflare-pages-limits": {
      "id": "cloudflare-pages-limits",
      "url": "https://developers.cloudflare.com/pages/platform/limits/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare Pages limits."
    },
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "Official Supabase billing documentation."
    }
  }
} satisfies RecommendationResponse

export const fixtureG = {
  "requirement": {
    "features": [
      "static-frontend",
      "file-uploads"
    ],
    "file_storage_bytes": 1000000000,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": 10000000000,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [],
      "unknown": [
        {
          "plan_id": "cloudflare-pages-free",
          "role": "static-frontend",
          "status": "unknown",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [
            {
              "reason_code": "limit-not-found",
              "outcome": "unknown",
              "limit": null,
              "other_period_limits": []
            },
            {
              "reason_code": "limit-period-mismatch",
              "outcome": "unknown",
              "limit": null,
              "other_period_limits": [
                {
                  "plan_id": "cloudflare-pages-free",
                  "metric": "bandwidth-bytes",
                  "period": "day",
                  "value": 1000000000,
                  "source_id": "cloudflare-pages-limits"
                }
              ]
            }
          ],
          "budget_check": null
        }
      ],
      "incompatible": []
    },
    {
      "role": "file-uploads",
      "compatible": [
        {
          "plan_id": "cloudflare-r2-free",
          "role": "file-uploads",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [
            {
              "reason_code": "within-limit",
              "outcome": "satisfied",
              "limit": {
                "plan_id": "cloudflare-r2-free",
                "metric": "file-storage-bytes",
                "period": "none",
                "value": 10000000000,
                "source_id": "cloudflare-r2-pricing"
              },
              "other_period_limits": []
            }
          ],
          "global_quantity_checks": [
            {
              "reason_code": "unlimited",
              "outcome": "satisfied",
              "limit": {
                "plan_id": "cloudflare-r2-free",
                "metric": "bandwidth-bytes",
                "period": "month",
                "value": null,
                "source_id": "cloudflare-r2-pricing"
              },
              "other_period_limits": []
            }
          ],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": [
        {
          "plan_id": "supabase-platform-free",
          "role": "file-uploads",
          "status": "incompatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [
            {
              "reason_code": "within-limit",
              "outcome": "satisfied",
              "limit": {
                "plan_id": "supabase-platform-free",
                "metric": "file-storage-bytes",
                "period": "none",
                "value": 1000000000,
                "source_id": "supabase-billing"
              },
              "other_period_limits": []
            }
          ],
          "global_quantity_checks": [
            {
              "reason_code": "exceeds-limit",
              "outcome": "violated",
              "limit": {
                "plan_id": "supabase-platform-free",
                "metric": "bandwidth-bytes",
                "period": "month",
                "value": 5000000000,
                "source_id": "supabase-billing"
              },
              "other_period_limits": []
            }
          ],
          "budget_check": null
        }
      ]
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [],
    "unknown": [
      {
        "key": "file-uploads=cloudflare-r2-free;static-frontend=cloudflare-pages-free",
        "assignments": [
          {
            "feature": "file-uploads",
            "plan_id": "cloudflare-r2-free",
            "status": "compatible"
          },
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "unknown"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free",
          "cloudflare-r2-free"
        ],
        "status": "unknown",
        "budget_check": null
      }
    ],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 1,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "cloudflare-pages-free": {
      "plan": {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare Pages plan.",
        "capabilities": [
          "static-hosting"
        ]
      },
      "service": {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "Static site hosting."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan includes 500 builds per month.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan allows one build at a time.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Builds time out after 20 minutes.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A Free plan site can contain up to 20,000 files.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A single Pages asset can be at most 25 MiB.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Requests to Pages Functions count toward the Workers plan quota.",
          "source_id": "cloudflare-pages-limits"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-pages-limits",
          "url": "https://developers.cloudflare.com/pages/platform/limits/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare Pages limits."
        }
      ]
    },
    "cloudflare-r2-free": {
      "plan": {
        "id": "cloudflare-r2-free",
        "service_id": "cloudflare-r2",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare R2 allowance.",
        "capabilities": [
          "file-storage"
        ]
      },
      "service": {
        "id": "cloudflare-r2",
        "provider_id": "cloudflare",
        "name": "R2",
        "slug": "r2",
        "description": "Object storage."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-r2-free",
          "statement": "The free tier includes 1 million Class A operations per month.",
          "source_id": "cloudflare-r2-pricing"
        },
        {
          "plan_id": "cloudflare-r2-free",
          "statement": "The free tier includes 10 million Class B operations per month.",
          "source_id": "cloudflare-r2-pricing"
        },
        {
          "plan_id": "cloudflare-r2-free",
          "statement": "The free tier applies only to Standard storage, and usage beyond the included amount is billed.",
          "source_id": "cloudflare-r2-pricing"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-r2-pricing",
          "url": "https://developers.cloudflare.com/r2/pricing/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare R2 pricing."
        }
      ]
    },
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "cloudflare-pages-limits": {
      "id": "cloudflare-pages-limits",
      "url": "https://developers.cloudflare.com/pages/platform/limits/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare Pages limits."
    },
    "cloudflare-r2-pricing": {
      "id": "cloudflare-r2-pricing",
      "url": "https://developers.cloudflare.com/r2/pricing/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare R2 pricing."
    },
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "Official Supabase billing documentation."
    }
  }
} satisfies RecommendationResponse

export const fixtureH = {
  "requirement": {
    "features": [
      "static-frontend",
      "database"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": 0
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [],
      "unknown": [
        {
          "plan_id": "cloudflare-pages-free",
          "role": "static-frontend",
          "status": "unknown",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": {
            "reason_code": "pricing-not-found",
            "outcome": "unknown",
            "pricing": null
          }
        }
      ],
      "incompatible": []
    },
    {
      "role": "database",
      "compatible": [],
      "unknown": [
        {
          "plan_id": "supabase-platform-free",
          "role": "database",
          "status": "unknown",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": {
            "reason_code": "pricing-not-found",
            "outcome": "unknown",
            "pricing": null
          }
        }
      ],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [
      {
        "key": "static-frontend=cloudflare-pages-free;budget=within-budget",
        "assignments": [
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "compatible"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free"
        ],
        "status": "compatible",
        "budget_check": {
          "budget_usd_cents": 1000,
          "priced_plan_ids": [
            "cloudflare-pages-free"
          ],
          "unpriced_plan_ids": [],
          "known_total_usd_cents": 500,
          "reason": "within-budget",
          "outcome": "satisfied"
        }
      }
    ],
    "unknown": [
      {
        "key": "database=supabase-platform-free;budget=pricing-not-found",
        "assignments": [
          {
            "feature": "database",
            "plan_id": "supabase-platform-free",
            "status": "unknown"
          }
        ],
        "plan_ids": [
          "supabase-platform-free"
        ],
        "status": "unknown",
        "budget_check": {
          "budget_usd_cents": 0,
          "priced_plan_ids": [],
          "unpriced_plan_ids": [
            "cloudflare-pages-free"
          ],
          "known_total_usd_cents": 0,
          "reason": "pricing-not-found",
          "outcome": "unknown"
        }
      }
    ],
    "incompatible": [
      {
        "key": "static-frontend=cloudflare-pages-free;budget=over-budget",
        "assignments": [
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "incompatible"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free"
        ],
        "status": "incompatible",
        "budget_check": {
          "budget_usd_cents": 500,
          "priced_plan_ids": [
            "cloudflare-pages-free"
          ],
          "unpriced_plan_ids": [],
          "known_total_usd_cents": 2000,
          "reason": "over-budget",
          "outcome": "violated"
        }
      }
    ],
    "blocked_roles": [],
    "combination_count": 3,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "cloudflare-pages-free": {
      "plan": {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare Pages plan.",
        "capabilities": [
          "static-hosting"
        ]
      },
      "service": {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "Static site hosting."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan includes 500 builds per month.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan allows one build at a time.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Builds time out after 20 minutes.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A Free plan site can contain up to 20,000 files.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A single Pages asset can be at most 25 MiB.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Requests to Pages Functions count toward the Workers plan quota.",
          "source_id": "cloudflare-pages-limits"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-pages-limits",
          "url": "https://developers.cloudflare.com/pages/platform/limits/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare Pages limits."
        }
      ]
    },
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "cloudflare-pages-limits": {
      "id": "cloudflare-pages-limits",
      "url": "https://developers.cloudflare.com/pages/platform/limits/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare Pages limits."
    },
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "Official Supabase billing documentation."
    }
  }
} satisfies RecommendationResponse

export const fixtureI = {
  "requirement": {
    "features": [
      "static-frontend"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": 10000000000,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [],
      "unknown": [
        {
          "plan_id": "period-mismatch-plan",
          "role": "static-frontend",
          "status": "unknown",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [
            {
              "reason_code": "limit-period-mismatch",
              "outcome": "unknown",
              "limit": null,
              "other_period_limits": [
                {
                  "plan_id": "period-mismatch-plan",
                  "metric": "bandwidth-bytes",
                  "period": "day",
                  "value": 1000000000,
                  "source_id": "period-mismatch-source"
                }
              ]
            }
          ],
          "budget_check": null
        }
      ],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 0,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {},
  "sources": {
    "period-mismatch-source": {
      "id": "period-mismatch-source",
      "url": "https://example.com/limits/day",
      "checked_at": "2026-09-30",
      "notes": ""
    }
  }
} satisfies RecommendationResponse


// Fixture J. Live response for {"features":["static-frontend","file-uploads"]}.
// composed, two stacks. Cloudflare Pages is shared. file-uploads is assigned to a different plan in each stack.
export const fixtureJ = {
  "requirement": {
    "features": [
      "static-frontend",
      "file-uploads"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "static-frontend",
      "compatible": [
        {
          "plan_id": "cloudflare-pages-free",
          "role": "static-frontend",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    },
    {
      "role": "file-uploads",
      "compatible": [
        {
          "plan_id": "cloudflare-r2-free",
          "role": "file-uploads",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        },
        {
          "plan_id": "supabase-platform-free",
          "role": "file-uploads",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [
      {
        "key": "file-uploads=cloudflare-r2-free;static-frontend=cloudflare-pages-free",
        "assignments": [
          {
            "feature": "file-uploads",
            "plan_id": "cloudflare-r2-free",
            "status": "compatible"
          },
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "compatible"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free",
          "cloudflare-r2-free"
        ],
        "status": "compatible",
        "budget_check": null
      },
      {
        "key": "file-uploads=supabase-platform-free;static-frontend=cloudflare-pages-free",
        "assignments": [
          {
            "feature": "file-uploads",
            "plan_id": "supabase-platform-free",
            "status": "compatible"
          },
          {
            "feature": "static-frontend",
            "plan_id": "cloudflare-pages-free",
            "status": "compatible"
          }
        ],
        "plan_ids": [
          "cloudflare-pages-free",
          "supabase-platform-free"
        ],
        "status": "compatible",
        "budget_check": null
      }
    ],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 2,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "cloudflare-pages-free": {
      "plan": {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare Pages plan.",
        "capabilities": [
          "static-hosting"
        ]
      },
      "service": {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "Static site hosting."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan includes 500 builds per month.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "The Free plan allows one build at a time.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Builds time out after 20 minutes.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A Free plan site can contain up to 20,000 files.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "A single Pages asset can be at most 25 MiB.",
          "source_id": "cloudflare-pages-limits"
        },
        {
          "plan_id": "cloudflare-pages-free",
          "statement": "Requests to Pages Functions count toward the Workers plan quota.",
          "source_id": "cloudflare-pages-limits"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-pages-limits",
          "url": "https://developers.cloudflare.com/pages/platform/limits/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare Pages limits."
        }
      ]
    },
    "cloudflare-r2-free": {
      "plan": {
        "id": "cloudflare-r2-free",
        "service_id": "cloudflare-r2",
        "name": "Free",
        "slug": "free",
        "description": "Free Cloudflare R2 allowance.",
        "capabilities": [
          "file-storage"
        ]
      },
      "service": {
        "id": "cloudflare-r2",
        "provider_id": "cloudflare",
        "name": "R2",
        "slug": "r2",
        "description": "Object storage."
      },
      "provider": {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "Edge network and developer platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "cloudflare-r2-free",
          "statement": "The free tier includes 1 million Class A operations per month.",
          "source_id": "cloudflare-r2-pricing"
        },
        {
          "plan_id": "cloudflare-r2-free",
          "statement": "The free tier includes 10 million Class B operations per month.",
          "source_id": "cloudflare-r2-pricing"
        },
        {
          "plan_id": "cloudflare-r2-free",
          "statement": "The free tier applies only to Standard storage, and usage beyond the included amount is billed.",
          "source_id": "cloudflare-r2-pricing"
        }
      ],
      "sources": [
        {
          "id": "cloudflare-r2-pricing",
          "url": "https://developers.cloudflare.com/r2/pricing/",
          "checked_at": "2026-09-30",
          "notes": "Official Cloudflare R2 pricing."
        }
      ]
    },
    "supabase-platform-free": {
      "plan": {
        "id": "supabase-platform-free",
        "service_id": "supabase-platform",
        "name": "Free",
        "slug": "free",
        "description": "Free Supabase plan.",
        "capabilities": [
          "serverless-functions",
          "database",
          "file-storage",
          "authentication",
          "realtime"
        ]
      },
      "service": {
        "id": "supabase-platform",
        "provider_id": "supabase",
        "name": "Platform",
        "slug": "platform",
        "description": "Database, auth, storage, and related backend services."
      },
      "provider": {
        "id": "supabase",
        "name": "Supabase",
        "slug": "supabase",
        "description": "Hosted Postgres and application backend platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes two projects.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 500 MB database size quota applies per project.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 1 GB storage quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The 5 GB egress quota applies per organization.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 50,000 monthly active users.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 500,000 Edge Function invocations.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 2,000,000 Realtime messages.",
          "source_id": "supabase-billing"
        },
        {
          "plan_id": "supabase-platform-free",
          "statement": "The Free plan includes 200 Realtime peak connections.",
          "source_id": "supabase-billing"
        }
      ],
      "sources": [
        {
          "id": "supabase-billing",
          "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
          "checked_at": "2026-09-30",
          "notes": "Official Supabase billing documentation."
        }
      ]
    }
  },
  "sources": {
    "cloudflare-pages-limits": {
      "id": "cloudflare-pages-limits",
      "url": "https://developers.cloudflare.com/pages/platform/limits/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare Pages limits."
    },
    "cloudflare-r2-pricing": {
      "id": "cloudflare-r2-pricing",
      "url": "https://developers.cloudflare.com/r2/pricing/",
      "checked_at": "2026-09-30",
      "notes": "Official Cloudflare R2 pricing."
    },
    "supabase-billing": {
      "id": "supabase-billing",
      "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
      "checked_at": "2026-09-30",
      "notes": "Official Supabase billing documentation."
    }
  }
} satisfies RecommendationResponse

// Fixture K. Live response for {"features":["backend-server"]}.
// Render web service. Two sources. Caveats reference those sources.
export const fixtureK = {
  "requirement": {
    "features": [
      "backend-server"
    ],
    "file_storage_bytes": null,
    "database_size_bytes": null,
    "monthly_bandwidth_bytes": null,
    "monthly_budget_usd_cents": null
  },
  "roles": [
    {
      "role": "backend-server",
      "compatible": [
        {
          "plan_id": "render-web-service-free",
          "role": "backend-server",
          "status": "compatible",
          "capability_check": {
            "reason_code": "capability-provided",
            "outcome": "satisfied"
          },
          "quantity_checks": [],
          "global_quantity_checks": [],
          "budget_check": null
        }
      ],
      "unknown": [],
      "incompatible": []
    }
  ],
  "composition": {
    "status": "composed",
    "compatible": [
      {
        "key": "backend-server=render-web-service-free",
        "assignments": [
          {
            "feature": "backend-server",
            "plan_id": "render-web-service-free",
            "status": "compatible"
          }
        ],
        "plan_ids": [
          "render-web-service-free"
        ],
        "status": "compatible",
        "budget_check": null
      }
    ],
    "unknown": [],
    "incompatible": [],
    "blocked_roles": [],
    "combination_count": 1,
    "unevaluated_features": []
  },
  "unevaluated_features": [],
  "plans": {
    "render-web-service-free": {
      "plan": {
        "id": "render-web-service-free",
        "service_id": "render-web-service",
        "name": "Free",
        "slug": "free",
        "description": "Free Render web service instance.",
        "capabilities": [
          "server-compute"
        ]
      },
      "service": {
        "id": "render-web-service",
        "provider_id": "render",
        "name": "Web Service",
        "slug": "web-service",
        "description": "Hosted web application compute."
      },
      "provider": {
        "id": "render",
        "name": "Render",
        "slug": "render",
        "description": "Application hosting platform."
      },
      "pricing": null,
      "caveats": [
        {
          "plan_id": "render-web-service-free",
          "statement": "Each workspace receives 750 Free instance hours per calendar month.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "When Free instance hours are exhausted, Free web services are suspended until the next month.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "A Free web service spins down after 15 minutes without inbound traffic.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "Spinning a Free web service back up takes about one minute.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "Free web services have an ephemeral filesystem.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "A persistent disk cannot be attached to a Free web service.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "A Free web service cannot scale beyond a single instance.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "Render may restart a Free web service at any time.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "Render says not to use Free instances for production applications.",
          "source_id": "render-free"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "The Free web service compute plan provides 0.1 CPU.",
          "source_id": "render-compute-plans"
        },
        {
          "plan_id": "render-web-service-free",
          "statement": "The Free web service compute plan provides 512 MB of RAM.",
          "source_id": "render-compute-plans"
        }
      ],
      "sources": [
        {
          "id": "render-compute-plans",
          "url": "https://render.com/docs/compute-plans",
          "checked_at": "2026-09-30",
          "notes": "Official Render compute plan specifications."
        },
        {
          "id": "render-free",
          "url": "https://render.com/docs/free",
          "checked_at": "2026-09-30",
          "notes": "Official Render Free instance documentation."
        }
      ]
    }
  },
  "sources": {
    "render-compute-plans": {
      "id": "render-compute-plans",
      "url": "https://render.com/docs/compute-plans",
      "checked_at": "2026-09-30",
      "notes": "Official Render compute plan specifications."
    },
    "render-free": {
      "id": "render-free",
      "url": "https://render.com/docs/free",
      "checked_at": "2026-09-30",
      "notes": "Official Render Free instance documentation."
    }
  }
} satisfies RecommendationResponse
