"""Error classes for Appnigma Integrations Client."""

from typing import Any, Optional


class AppnigmaAPIError(Exception):
    """Custom exception for Appnigma API errors."""

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        response_body: Optional[Any] = None
    ):
        """
        Initialize AppnigmaAPIError.

        Args:
            status_code: HTTP status code
            error: Error type/code
            message: Human-readable error message
            response_body: Full response body from API
        """
        super().__init__(message)
        self.status_code = status_code
        self.error = error
        self.message = message
        self.response_body = response_body

    def get_details(self) -> dict:
        """
        Get error details including rate limit information if available.

        Returns:
            Dictionary with error details
        """
        details = {
            'error': self.error,
            'message': self.message
        }

        if self.response_body and isinstance(self.response_body, dict):
            if 'planLimit' in self.response_body:
                details['planLimit'] = self.response_body.get('planLimit')
                details['currentUsage'] = self.response_body.get('currentUsage')
                details['offerings'] = self.response_body.get('offerings')

        return details
