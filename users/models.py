from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    username = None
    nickname = models.CharField(max_length=128)
    email = models.EmailField(unique=True, max_length=254)
    avatar = models.ImageField(upload_to='avatars', blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        
    def __str__(self):
        return self.nickname