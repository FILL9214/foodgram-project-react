from .permissions import IsAuthorOrReadOnly
from .serializers import SubscribeRecipeSerializer
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from recipes.models import Recipe


class PermissionAndPaginationMixin:
    """Миксина для списка тегов и ингридиентов."""

    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = None


class GetObjectMixin:
    """Миксина для удаления/добавления рецептов избранных/корзины."""

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (AllowAny,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe
