import io
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.db.models.signals import post_save
from django.dispatch import receiver
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.conf import settings
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag, User)
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer,
                          SubscribeSerializer, TagSerializer,
                          UserListSerializer)
from .mixins import PermissionAndPaginationMixin

FILENAME = 'shoppingcart.pdf'


class AddAndDeleteSubscribe(
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):
    """Подписка и отписка от пользователя."""

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True), )

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        subs = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.follower.filter(author=instance).delete()


class UsersViewSet(UserViewSet):
    """Пользователи."""

    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.annotate(
            is_subscribed=Exists(
                self.request.user.follower.filter(
                    author=OuterRef('id'))
            )).prefetch_related(
                'follower', 'following'
        ) if self.request.user.is_authenticated else User.objects.annotate(
            is_subscribed=Value(False))

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Получить на кого пользователь подписан."""

        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    """Рецепты."""

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        return Recipe.objects.annotate(
            is_favorited=Exists(
                FavoriteRecipe.objects.filter(
                    user=self.request.user, recipe=OuterRef('id'))),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef('id')))
        ).select_related('author').prefetch_related(
            'tags', 'ingredients',
            'shopping_cart', 'favorite_recipe'
        ) if self.request.user.is_authenticated else Recipe.objects.annotate(
            is_in_shopping_cart=Value(False),
            is_favorited=Value(False),
        ).select_related('author').prefetch_related(
            'tags', 'ingredients',
            'shopping_cart', 'favorite_recipe')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @receiver(post_save, sender=User)
    def create_shopping_cart_obj(
            sender, instance, created, **kwargs):
        if created:
            return ShoppingCart.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def create_favorite_recipe_obj(
            sender, instance, created, **kwargs):
        if created:
            return FavoriteRecipe.objects.create(user=instance)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'POST':
            self.request.user.favorite_recipe.recipe.add(instance)
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            self.request.user.favorite_recipe.recipe.remove(instance)
            return Response(
                'Рецепт успешно удалён из избранного.',
                status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'POST':
            self.request.user.shopping_cart.recipe.add(instance)
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            self.request.user.shopping_cart.recipe.remove(instance)
            return Response(
                'Рецепт успешно удалён из списка покупок.',
                status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def create_shopping_cart(request):
        """Создаем список с ингредиентами."""

        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        data_path = settings.BASE_DIR
        pdfmetrics.registerFont(TTFont('Arial', f'{data_path}/data/arial.ttf'))
        x_position, y_position = 50, 800
        shopping_cart = (
            request.user.shopping_cart.recipe.
            values(
                'ingredients__name',
                'ingredients__measurement_unit'
            ).annotate(amount=Sum('recipe__amount')).order_by())
        page.setFont('Arial', 14)
        if shopping_cart:
            indent = 20
            page.drawString(x_position, y_position, 'Cписок покупок:')
            for index, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - indent,
                    f'{index}. {recipe["ingredients__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredients__measurement_unit"]}.')
                y_position -= 15
                if y_position <= 50:
                    page.showPage()
                    y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename=FILENAME)
        page.setFont('Arial', 24)
        page.drawString(
            x_position,
            y_position,
            'Cписок покупок пуст!')
        page.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=FILENAME)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        return self.create_shopping_cart(request)


class TagsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):
    """Список тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):
    """Список ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
