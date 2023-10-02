from .permissions import IsAuthorOrReadOnly


class PermissionAndPaginationMixin:
    """Миксина для списка тегов и ингридиентов."""

    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = None
