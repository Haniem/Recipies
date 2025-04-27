from django.db import models

# Create your models here.

class FormData(models.Model):
    email = models.EmailField()
    password = models.CharField(max_length=128)
    checkbox = models.BooleanField(default=False)

    def __str__(self):
        return self.email

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название ингредиента")

    def __str__(self):
        return self.name

class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название рецепта")
    ingredients = models.ManyToManyField(Ingredient, related_name='recipes', verbose_name="Ингредиенты")
    cooking_time = models.CharField(max_length=50, verbose_name="Время приготовления")
    instructions = models.TextField(verbose_name="Инструкции")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
