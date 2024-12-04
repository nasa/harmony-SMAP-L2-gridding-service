"""Module defining custom exceptions."""


class SMAPL2GridderError(Exception):
    """Base error class for exceptions raised by smap_l2_gridder library."""

    def __init__(self, message=None):
        """All Harmony SMAP L2 gridding service errors have a message field."""
        self.message = message


class InvalidGPDError(SMAPL2GridderError):
    """Raised if an invalid GPD is used."""
