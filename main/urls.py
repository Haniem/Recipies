from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_recipes, name='index'),  # Главная страница
    path('add/', views.add_recipe, name='add_recipe'),  # Страница добавления рецепта
    path('import-page/', views.import_page, name='import_page'),  # Страница импорта
    path('export/', views.export_to_xml, name='export_to_xml'),
    path('import/', views.import_from_xml, name='import_from_xml'),
    path('download/xml/', views.download_recipes_xml, name='download_recipes_xml'),
    path('download/db/', views.download_recipes_db, name='download_recipes_db'),
    path('ajax/add-ingredient/', views.add_ingredient_ajax, name='add_ingredient_ajax'),
    path('edit/<int:pk>/', views.edit_recipe, name='edit_recipe'),
    path('edit-xml/<int:index>/', views.edit_recipe_xml, name='edit_recipe_xml'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
]
