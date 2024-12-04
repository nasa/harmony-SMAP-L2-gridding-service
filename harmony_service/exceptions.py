"""Define harmony service errors raised by Harmony SMAP L2 gridding service."""

from harmony_service_lib.util import HarmonyException

SERVICE_NAME = 'harmony-smap-l2-gridder'


class SMAPL2GridderServiceError(HarmonyException):
    """Base service exception."""

    def __init__(self, message=None):
        """All service errors are assocated with SERVICE_NAME."""
        super().__init__(message=message, category=SERVICE_NAME)
