from django.contrib.auth.models import AbstractUser
from django.db import models
from backend.constants import MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(
        'Email',
        max_length=MAX_LENGTH,
        unique=True,)
    first_name = models.CharField(
        'Имя',
        max_length=150)
    last_name = models.CharField(
        'Фамилия',
        max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email
