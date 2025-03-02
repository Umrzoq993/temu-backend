from rest_framework import permissions


class IsAdminOrOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff  # Simplified example


class IsAdminOrOperatorBoss(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsAdminOrCourierBoss(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.role == 'Admin' or user.role == 'Courier Boss')


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.role == 'Admin'


class IsCourierBoss(permissions.BasePermission):
    """
    Custom permission to only allow courier bosses to assign products.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Courier Boss'
