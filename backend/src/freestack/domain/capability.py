from enum import StrEnum


class CapabilityKey(StrEnum):
    """Fixed capability vocabulary. This is not a stored entity."""

    STATIC_HOSTING = "static-hosting"
    SERVER_COMPUTE = "server-compute"
    SERVERLESS_FUNCTIONS = "serverless-functions"
    DATABASE = "database"
    FILE_STORAGE = "file-storage"
    AUTHENTICATION = "authentication"
    REALTIME = "realtime"
    SCHEDULED_JOBS = "scheduled-jobs"
