from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, RecipeForm, RecipeStepFormSet, RecipeIngredientForm, RecipeStepForm
from .models import User, RecipeIngredient, RecipeStep, ListIngredient, Recipe, Genre, Favorite 
from django.shortcuts import get_object_or_404
from django.forms import formset_factory, modelformset_factory 
from django.contrib import messages
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse, HttpResponseBadRequest 


def index(request):
    return render(request, 'index.html')



def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():

            user = form.save() 

            login(request, user) 
            
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile') 
        else:

            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email_or_phone = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = None
            try:
                # сначала по email
                user_obj = User.objects.get(email=email_or_phone)
                user = authenticate(request, email=user_obj.email, password=password)
            except User.DoesNotExist:
                try:
                    user_obj = User.objects.get(phone_num=email_or_phone)
                    user = authenticate(request, email=user_obj.email, password=password)
                except User.DoesNotExist:
                    user = None
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect('admin_profile')
                return redirect('profile')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def profile_view(request):
    if request.user.is_superuser:
        return redirect('admin_profile')
    
    user_recipes = request.user.recipes.all().order_by('-created_at')

    context = {
        'recipes': user_recipes
    }
    return render(request, 'profile.html', context)

@login_required
def admin_profile_view(request):
    if not request.user.is_superuser:
        return redirect('profile')
    return render(request, 'admin_profile.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        if 'remove_avatar' in request.POST:
            if user.avatar:
                user.avatar.delete(save=False)  
                user.avatar = None
                user.save()
            return redirect('profile_edit')

        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'profile_edit.html', {'form': form})



@login_required
def recipe_create_view(request):
    IngredientFormSet = formset_factory(RecipeIngredientForm, extra=1, can_delete=True)
    RecipeStepFormSet_initial = modelformset_factory(
        RecipeStep, 
        form=RecipeStepForm, 
        extra=1, 
        can_delete=True
    )

    if request.method == 'POST':
        submit_status = request.POST.get('submit_status', 'draft') 

        form = RecipeForm(request.POST, request.FILES)

        form.data = form.data.copy()
        form.data['status_field'] = submit_status
        
        step_formset = RecipeStepFormSet_initial(request.POST, request.FILES, queryset=RecipeStep.objects.none())
        ingredient_formset = IngredientFormSet(request.POST, prefix='ingr')

        if form.is_valid() and step_formset.is_valid() and ingredient_formset.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user

            recipe.save()
            form.save_m2m() 
            
            # Сохранение этапов готовки
            RecipeStep.objects.filter(recipe=recipe).delete() 
            for order, step_form in enumerate(step_formset):
                if step_form.cleaned_data and not step_form.cleaned_data.get('DELETE', False):
                    step = step_form.save(commit=False)
                    step.recipe = recipe
                    step.order = order + 1 # Устанавливаем порядок
                    step.save()

            # Сохранение ингредиентов
            RecipeIngredient.objects.filter(recipe=recipe).delete() 
            for ingr_form in ingredient_formset:
                if ingr_form.cleaned_data and not ingr_form.cleaned_data.get('DELETE', False):
                    ingredient_name = ingr_form.cleaned_data['ingredient_name'] 
                    
                    list_ingredient, created = ListIngredient.objects.get_or_create(
                        name__iexact=ingredient_name, 
                        defaults={'name': ingredient_name}
                    )
                    
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=list_ingredient,  
                        quantity=ingr_form.cleaned_data['quantity'],
                        unit=ingr_form.cleaned_data['unit'],
                    )
            
            status_display = "опубликован" if submit_status == 'published' else "сохранен как черновик"
            messages.success(request, f'Рецепт успешно {status_display}!')
            return redirect('profile') # Перенаправляем на профиль, где пользователь увидит черновик

        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = RecipeForm()
        step_formset = RecipeStepFormSet_initial(queryset=RecipeStep.objects.none()) 
        ingredient_formset = IngredientFormSet(prefix='ingr')
    pass
    context = {
        'form': form,
        'formset': step_formset, 
        'ingredient_formset': ingredient_formset, 
    }
    return render(request, 'recipes/recipe_create.html', context)


@login_required
def recipe_edit_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    IngredientFormSet = formset_factory(RecipeIngredientForm, extra=0, can_delete=True)
    RecipeStepFormSet_Model = modelformset_factory(
        RecipeStep, 
        form=RecipeStepForm, 
        extra=0, 
        can_delete=True,
    )

    if request.method == 'POST':
        submit_status = request.POST.get('submit_status', 'draft') 

        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        form.data = form.data.copy()
        form.data['status_field'] = submit_status
        
        step_formset = RecipeStepFormSet_Model(request.POST, request.FILES, queryset=recipe.steps.all())
        ingredient_formset = IngredientFormSet(request.POST, prefix='ingr')

        if form.is_valid() and step_formset.is_valid() and ingredient_formset.is_valid():
             
            recipe = form.save(commit=False)
            recipe.save()
            form.save_m2m() 
            
            RecipeStep.objects.filter(recipe=recipe).delete() 
            for order, step_form in enumerate(step_formset):
                if step_form.cleaned_data and not step_form.cleaned_data.get('DELETE', False):
                    step = step_form.save(commit=False)
                    step.recipe = recipe
                    step.order = order + 1
                    step.save()
                    
            RecipeIngredient.objects.filter(recipe=recipe).delete() 
            for ingr_form in ingredient_formset:
                if ingr_form.cleaned_data and not ingr_form.cleaned_data.get('DELETE', False):
                    ingredient_name = ingr_form.cleaned_data['ingredient_name'] 
                    
                    list_ingredient, created = ListIngredient.objects.get_or_create(
                        name__iexact=ingredient_name, 
                        defaults={'name': ingredient_name}
                    )
                    
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=list_ingredient,  
                        quantity=ingr_form.cleaned_data['quantity'],
                        unit=ingr_form.cleaned_data['unit'],
                    )
                    
            status_display = "опубликован" if submit_status == 'published' else "обновлен как черновик"
            messages.success(request, f'Рецепт успешно {status_display}!')
            return redirect('profile') 
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')


    else:
        form = RecipeForm(instance=recipe, initial={'status_field': recipe.status}) 
        step_formset = RecipeStepFormSet_Model(queryset=recipe.steps.all())
        
        initial_ingredients = [{'ingredient_name': ri.ingredient.name, 'quantity': ri.quantity, 'unit': ri.unit}
                               for ri in recipe.recipe_ingredients.all()]
        ingredient_formset = IngredientFormSet(prefix='ingr', initial=initial_ingredients)

    context = {
        'form': form,
        'formset': step_formset,
        'ingredient_formset': ingredient_formset,
        'recipe': recipe,
        'recipe_details_fields': [
            form['portions'],
            form['calories'],
            form['estimated_cost'],
        ]
    }
    return render(request, 'recipes/recipe_edit.html', context)

def recipe_detail_view(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.select_related('user').prefetch_related('genres', 'recipe_ingredients__ingredient', 'steps'), 
        pk=pk
    )
    
    
    ingredients = recipe.recipe_ingredients.all()
    steps = recipe.steps.all().order_by('order')

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
    }
    return render(request, 'recipes/recipe_detail.html', context)


def user_profile_view(request, user_id):
    user_to_show = get_object_or_404(User, pk=user_id)
    user_recipes = user_to_show.recipes.filter(status='published').order_by('-created_at')
    context = {
        'profile_user': user_to_show,
        'recipes': user_recipes,
    }
    return render(request, 'users/profile.html', context)



def recipe_list_view(request):
    recipes = Recipe.objects.filter(status='published').select_related('user').prefetch_related('genres').order_by('-created_at')
    all_genres = Genre.objects.annotate(
        published_recipe_count=Count(
            'recipes', 
            filter=Q(recipes__status='published')
        )
    ).order_by('name')

    selected_genre_id = request.GET.get('genre')
    selected_genre_name = None
    
    if selected_genre_id:
        try:
            recipes = recipes.filter(genres__id=selected_genre_id)
            selected_genre_name = Genre.objects.get(id=selected_genre_id).name
        except Genre.DoesNotExist:
            pass 
            
    search_query = request.GET.get('q')
    if search_query:
        recipes = recipes.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        ).distinct()

    context = {
        'recipes': recipes,
        'all_genres': all_genres,
        'selected_genre_id': selected_genre_id,
        'selected_genre_name': selected_genre_name,
        'search_query': search_query,
    }
    return render(request, 'recipes/recipe_list.html', context)


@login_required
def toggle_favorite(request, recipe_id):

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Требуется авторизация'}, status=401)
    
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user = request.user
    
    try:
        favorite = Favorite.objects.get(user=user, recipe=recipe)
        favorite.delete() # Удаляем из избранного
        is_favorited = False
        message = f'Рецепт "{recipe.title}" удален из избранного.'
        
    except Favorite.DoesNotExist:
        # Если записи нет, создаем ее
        Favorite.objects.create(user=user, recipe=recipe)
        is_favorited = True
        message = f'Рецепт "{recipe.title}" добавлен в избранное.'
        
    return JsonResponse({
        'success': True,
        'is_favorited': is_favorited,
        'message': message,
        'recipe_id': recipe_id,
    })

def recipe_detail_view(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.select_related('user').prefetch_related('genres', 'recipe_ingredients__ingredient', 'steps'), 
        pk=pk
    )
    
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, recipe=recipe).exists()

    ingredients = recipe.recipe_ingredients.all()
    steps = recipe.steps.all().order_by('order')

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
        'is_favorited': is_favorited, 
    }
    return render(request, 'recipes/recipe_detail.html', context)

@login_required
def favorite_recipes_view(request):

    favorite_list = Favorite.objects.filter(user=request.user).select_related('recipe', 'recipe__user').order_by('-added_at')
    
    recipes = [fav.recipe for fav in favorite_list]

    context = {
        'recipes': recipes,
        'title': 'Избранные рецепты'
    }
    return render(request, 'recipes/favorite_recipes.html', context)

