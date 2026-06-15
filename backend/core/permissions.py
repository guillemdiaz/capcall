from rest_framework.permissions import BasePermission


class IsFundManager(BasePermission):
    """Grants access only to staff users (Fund Managers)"""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "is_staff")
            and request.user.is_staff
        )


class IsOwnerOrFundManager(BasePermission):
    """Allows access only to the owner of the object or a Fund Manager"""

    def has_object_permission(self, request, view, obj):
        return getattr(request.user, "is_staff", False) or obj == request.user
