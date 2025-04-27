from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import xml.etree.ElementTree as ET
from io import BytesIO
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from .models import Recipe, Ingredient, FormData
from django.contrib import messages


def toggle_theme(request):
    if request.method == 'POST':
        current_theme = request.COOKIES.get('theme', 'light')
        new_theme = 'dark' if current_theme == 'light' else 'light'
        current_path = request.POST.get('current_path', '/')
        response = redirect(current_path)
        response.set_cookie('theme', new_theme, max_age=3600)
        return response
    return redirect('/')

def export_to_xml(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        ingredient_ids = request.POST.getlist('ingredients')
        instructions = request.POST.get('instructions')
        cooking_time = request.POST.get('cooking_time')
        storage_type = request.POST.get('storage_type', 'xml')

        # Получаем объекты ингредиентов
        selected_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)

        if storage_type == 'database':
            recipe = Recipe.objects.create(
                name=name,
                cooking_time=cooking_time,
                instructions=instructions
            )
            recipe.ingredients.set(selected_ingredients)
            messages.success(request, "Рецепт успешно добавлен в базу данных!")
            return redirect('index')
        else:
            file_path = os.path.join(settings.BASE_DIR, 'uploads', 'recipes.xml')
            if os.path.exists(file_path):
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                except ET.ParseError:
                    root = ET.Element("recipes")
            else:
                root = ET.Element("recipes")
            recipe_elem = ET.SubElement(root, "recipe")
            ET.SubElement(recipe_elem, "name").text = name
            ingredients_elem = ET.SubElement(recipe_elem, "ingredients")
            for ingredient in selected_ingredients:
                ET.SubElement(ingredients_elem, "ingredient").text = ingredient.name
            ET.SubElement(recipe_elem, "instructions").text = instructions
            ET.SubElement(recipe_elem, "cooking_time").text = cooking_time
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            messages.success(request, "Рецепт успешно добавлен в файл XML!")
            return redirect('index')
    return HttpResponse("Метод не разрешен", status=405)

def download_recipes_xml(request):
    file_path = os.path.join(settings.BASE_DIR, 'uploads', 'recipes.xml')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='recipes.xml')
    return HttpResponse("Файл не найден", status=404)

def download_recipes_db(request):
    # Генерируем XML из БД и отдаем как файл
    recipes = Recipe.objects.all()
    root = ET.Element("recipes")
    for recipe in recipes:
        recipe_elem = ET.SubElement(root, "recipe")
        ET.SubElement(recipe_elem, "name").text = recipe.name
        ingredients_elem = ET.SubElement(recipe_elem, "ingredients")
        for ingredient in recipe.ingredients.all():
            ET.SubElement(ingredients_elem, "ingredient").text = ingredient.name
        ET.SubElement(recipe_elem, "instructions").text = recipe.instructions
        ET.SubElement(recipe_elem, "cooking_time").text = recipe.cooking_time
    xml_bytes = BytesIO()
    tree = ET.ElementTree(root)
    tree.write(xml_bytes, encoding='utf-8', xml_declaration=True)
    xml_bytes.seek(0)
    return FileResponse(xml_bytes, as_attachment=True, filename='recipes_from_db.xml')

@csrf_exempt
def import_from_xml(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            # Определяем путь к фиксированному файлу recipes.xml
            fixed_filename = 'recipes.xml'
            upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            fixed_filepath = os.path.join(upload_dir, fixed_filename)
            
            # Читаем содержимое загруженного файла
            uploaded_file = request.FILES['file']
            file_content = uploaded_file.read()
            
            # Сохраняем содержимое в фиксированный файл (перезаписываем если существует)
            with open(fixed_filepath, 'wb') as f:
                f.write(file_content)
            
            return HttpResponse(f"Данные успешно сохранены в {fixed_filename}", status=200)
        except Exception as e:
            return HttpResponse(f"Ошибка: {str(e)}", status=500)
    return HttpResponse("Неверный запрос", status=400)

def all_recipes(request):
    # Рецепты из базы данных
    db_recipes = []
    for recipe in Recipe.objects.all():
        db_recipes.append({
            'pk': recipe.pk,
            'name': recipe.name,
            'ingredients': [i.name for i in recipe.ingredients.all()],
            'instructions': recipe.instructions,
            'cooking_time': recipe.cooking_time,
            'source': 'База данных',
        })

    # Рецепты из XML
    xml_recipes = []
    file_path = os.path.join(settings.BASE_DIR, 'uploads', 'recipes.xml')
    if os.path.exists(file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for recipe_elem in root.findall('recipe'):
                name = recipe_elem.findtext('name', default='')
                ingredients = [i.text for i in recipe_elem.find('ingredients').findall('ingredient')] if recipe_elem.find('ingredients') is not None else []
                instructions = recipe_elem.findtext('instructions', default='')
                cooking_time = recipe_elem.findtext('cooking_time', default='')
                xml_recipes.append({
                    'pk': None,  # Для XML всегда None
                    'name': name,
                    'ingredients': ingredients,
                    'instructions': instructions,
                    'cooking_time': cooking_time,
                    'source': 'XML',
                })
        except Exception:
            pass
    all_recipes = db_recipes + xml_recipes
    return render(request, 'main/index.html', {'all_recipes': all_recipes})

def add_ingredient_ajax(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            ingredient, created = Ingredient.objects.get_or_create(name=name)
            ingredients = list(Ingredient.objects.all().order_by('name').values('id', 'name'))
            return JsonResponse({'success': True, 'ingredients': ingredients, 'added_id': ingredient.id})
    return JsonResponse({'success': False})

def edit_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    ingredients = Ingredient.objects.all().order_by('name')
    if request.method == 'POST':
        recipe.name = request.POST.get('name')
        recipe.cooking_time = request.POST.get('cooking_time')
        recipe.instructions = request.POST.get('instructions')
        ingredient_ids = request.POST.getlist('ingredients')
        selected_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        recipe.save()
        recipe.ingredients.set(selected_ingredients)
        return redirect('all_recipes')
    selected_ids = recipe.ingredients.values_list('id', flat=True)
    return render(request, 'main/edit_recipe.html', {
        'recipe': recipe,
        'ingredients': ingredients,
        'selected_ids': selected_ids,
        'is_xml': False
    })

def edit_recipe_xml(request, index):
    file_path = os.path.join(settings.BASE_DIR, 'uploads', 'recipes.xml')
    tree = ET.parse(file_path)
    root = tree.getroot()
    recipes = root.findall('recipe')
    if index < 0 or index >= len(recipes):
        return HttpResponse('Рецепт не найден', status=404)
    recipe_elem = recipes[index]
    if request.method == 'POST':
        recipe_elem.find('name').text = request.POST.get('name')
        recipe_elem.find('instructions').text = request.POST.get('instructions')
        recipe_elem.find('cooking_time').text = request.POST.get('cooking_time')
        # Обновляем ингредиенты
        new_ingredients = request.POST.getlist('ingredients')
        ingredients_elem = recipe_elem.find('ingredients')
        # Очищаем старые
        for ing in list(ingredients_elem):
            ingredients_elem.remove(ing)
        # Добавляем новые
        for ing_name in new_ingredients:
            ET.SubElement(ingredients_elem, 'ingredient').text = ing_name
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        return redirect('all_recipes')
    # Для формы: все ингредиенты из файла и из базы
    all_ingredients = set(ing.text for r in recipes for ing in (r.find('ingredients').findall('ingredient') if r.find('ingredients') is not None else []))
    db_ingredients = set(Ingredient.objects.values_list('name', flat=True))
    ingredients = sorted(list(all_ingredients | db_ingredients))
    selected_ingredients = [i.text for i in recipe_elem.find('ingredients').findall('ingredient')]
    return render(request, 'main/edit_recipe.html', {
        'recipe': {
            'name': recipe_elem.findtext('name', ''),
            'instructions': recipe_elem.findtext('instructions', ''),
            'cooking_time': recipe_elem.findtext('cooking_time', ''),
        },
        'ingredients': ingredients,
        'selected_ids': selected_ingredients,
        'is_xml': True,
        'xml_index': index
    })

def add_recipe(request):
    theme = request.COOKIES.get('theme', 'light')
    ingredients = Ingredient.objects.all().order_by('name')
    return render(request, 'main/add_recipe.html', {'theme': theme, 'ingredients': ingredients})

def import_page(request):
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'main/import_page.html', {'theme': theme})