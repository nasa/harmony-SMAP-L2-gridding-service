"""Define harmony service errors raised by SMAP-L2-Gridding-Service."""

from harmony_service_lib.util import HarmonyException

SERVICE_NAME = 'Harmony-SMAP-L2-Gridder'


class SMAPL2GridderServiceError(HarmonyException):
    """Base service exception."""

    def __init__(self, message=None):
        """All service errors are assocated with SERVICE_NAME."""
        super().__init__(message=message, category=SERVICE_NAME)
