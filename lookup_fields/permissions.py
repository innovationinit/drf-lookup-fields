"""Permission utils for customizable lookup fields."""

from typing import (
    List,
    Optional,
)


class WithPermissions(str):

    """Customizable lookup field with permission"""

    permissions: List[str]

    def __new__(cls, *args, permissions: Optional[List[str]] = None, **kwargs):
        new = super().__new__(cls, *args, **kwargs)
        new.permissions = permissions or []
        return new

    def has_permission(self, user):
        """Check is user is authenticated and has needed permissions."""
        if not user.is_authenticated:
            return False
        if not user.has_perms(self.permissions):
            return False
        return True
