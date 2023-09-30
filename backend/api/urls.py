from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (AddAndDeleteSubscribe,
                       IngredientsViewSet,
                       RecipesViewSet, TagsViewSet, UsersViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet)
router.register('tags', TagsViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipesViewSet)


urlpatterns = [
    path(
        'users/<int:user_id>/subscribe/',
        AddAndDeleteSubscribe.as_view(),
        name='subscribe'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
