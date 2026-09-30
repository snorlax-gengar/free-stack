from enum import StrEnum


class Feature(StrEnum):
    """A project capability the user asked for.

    This is not a catalog ``CapabilityKey``. Some features have no catalog
    capability and stay unevaluated.
    """

    STATIC_FRONTEND = "static-frontend"
    BACKEND_SERVER = "backend-server"
    BACKEND_FUNCTIONS = "backend-functions"
    DATABASE = "database"
    FILE_UPLOADS = "file-uploads"
    AUTHENTICATION = "authentication"
    REALTIME = "realtime"
    SCHEDULED_JOBS = "scheduled-jobs"
    AI_API = "ai-api"
