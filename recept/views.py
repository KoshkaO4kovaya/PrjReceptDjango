from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, RecipeForm, RecipeStepFormSet, RecipeIngredientForm, RecipeStepForm, ReviewForm 
from .models import User, RecipeIngredient, RecipeStep, ListIngredient, Recipe, Genre, Favorite,Review 
from django.shortcuts import get_object_or_404
from django.forms import formset_factory, modelformset_factory
from django import forms
from django.contrib import messages
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from .forms import AdminUserEditForm 


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
    return render(request, 'admin/admin_profile.html')

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

        is_valid = form.is_valid() and step_formset.is_valid() and ingredient_formset.is_valid()

        if is_valid and submit_status == 'pending':
            
            # Проверка на наличие ингредиентов
            valid_ingredients = [ingr_form for ingr_form in ingredient_formset if ingr_form.cleaned_data and not ingr_form.cleaned_data.get('DELETE', False)]
            if not valid_ingredients:
                messages.error(request, 'Для публикации необходимо добавить хотя бы один ингредиент.')
                is_valid = False
            
        if is_valid:
            recipe = form.save(commit=False)
            recipe.user = request.user
            

            recipe.status = submit_status
            
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
            
            status_display = "отправлен на модерацию" if recipe.status == 'pending' else "сохранен как черновик"
            messages.success(request, f'Рецепт успешно {status_display}!')
            return redirect('profile') 

        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')

    else:
        form = RecipeForm()
        step_formset = RecipeStepFormSet_initial(queryset=RecipeStep.objects.none()) 
        ingredient_formset = IngredientFormSet(prefix='ingr')
        
    context = {
        'form': form,
        'formset': step_formset, 
        'ingredient_formset': ingredient_formset, 
    }
    return render(request, 'recipes/recipe_create.html', context)

@login_required
def recipe_edit_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    
    # Запрет редактирования, если рецепт на модерации
    if recipe.status == 'pending':
        messages.warning(request, 'Рецепт находится на модерации. Дождитесь решения администратора.')
        return redirect('profile')

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

        is_valid = form.is_valid() and step_formset.is_valid() and ingredient_formset.is_valid()

        if is_valid and submit_status == 'pending':
            
            valid_ingredients = [ingr_form for ingr_form in ingredient_formset if ingr_form.cleaned_data and not ingr_form.cleaned_data.get('DELETE', False)]
            if not valid_ingredients:
                messages.error(request, 'Для публикации необходимо добавить хотя бы один ингредиент.')
                is_valid = False
            
        
        if is_valid:
             
            recipe = form.save(commit=False)
            recipe.status = submit_status 
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
                     
            status_display = "отправлен на модерацию" if submit_status == 'pending' else "обновлен как черновик"
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

@login_required
@require_POST
def recipe_delete_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    recipe_title = recipe.title
    recipe.delete()
    messages.success(request, f'Рецепт "{recipe_title}" успешно удален.')
    return redirect('profile')


def recipe_detail_view(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.select_related('user').prefetch_related('genres', 'recipe_ingredients__ingredient', 'steps', 'reviews'), 
        pk=pk
    )
    
    is_owner = request.user.is_authenticated and recipe.user == request.user
    is_admin = request.user.is_superuser if request.user.is_authenticated else False

    if recipe.status != 'published' and not (is_owner or is_admin):
        if recipe.status == 'pending':
            messages.warning(request, 'Этот рецепт находится на модерации и пока недоступен для просмотра.')
        elif recipe.status == 'rejected':
             messages.error(request, 'Этот рецепт был отклонен модератором и недоступен для публичного просмотра.')
        else:
             messages.warning(request, 'Этот рецепт еще не опубликован.')
             
        if not is_owner and not is_admin:
            return redirect('recipe_list') 


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
        'is_owner': is_owner, 
        'is_admin': is_admin,
    }
    return render(request, 'recipes/recipe_detail.html', context)

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
        favorite.delete() 
        is_favorited = False
        message = f'Рецепт "{recipe.title}" удален из избранного.'
        
    except Favorite.DoesNotExist:
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


# админка:

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_profile_view(request):
    total_users = User.objects.count()
    total_published_recipes = Recipe.objects.filter(status='published').count()
    total_pending_recipes = Recipe.objects.filter(status='pending').count() 

    context = {
        'total_users': total_users,
        'total_published_recipes': total_published_recipes,
        'total_pending_recipes': total_pending_recipes, \

    }
    return render(request, 'admin/admin_profile.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_users_list_view(request):
    users = User.objects.all().order_by('email')
    context = {'users': users}
    return render(request, 'admin/users_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_recipes_list_view(request):
    recipes = Recipe.objects.select_related('user').prefetch_related('genres').order_by('-created_at')
    context = {'recipes': recipes}
    return render(request, 'admin/recipes_list.html', context)


# админка

class RecipeGenreForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['genres']
        widgets = {
            'genres': forms.CheckboxSelectMultiple(),
        }

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_edit_recipe_genres(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = RecipeGenreForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Жанры успешно обновлены.')
            return redirect('admin_recipes_list')
    else:
        form = RecipeGenreForm(instance=recipe)

    context = {'form': form, 'recipe': recipe}
    return render(request, 'admin/edit_recipe_genres.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def admin_add_genre(request):
    name = request.POST.get('name', '').strip()
    error = None
    if name:
        exists = Genre.objects.filter(name__iexact=name).exists()
        if exists:
            error = "Жанр с таким названием уже существует."
        else:
            Genre.objects.create(name=name)
            messages.success(request, f'Жанр "{name}" успешно добавлен.')
    else:
        error = "Название жанра не может быть пустым."
    recipe_pk = request.GET.get('recipe_pk') or request.POST.get('recipe_pk')

    if not recipe_pk:
        return redirect('admin_profile')

    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    form = RecipeGenreForm(instance=recipe)
    context = {'form': form, 'recipe': recipe, 'genre_error': error}
    return render(request, 'admin/edit_recipe_genres.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_moderation_list_view(request):
    recipes = Recipe.objects.filter(status='pending').select_related('user').prefetch_related('genres').order_by('-created_at')
    context = {'recipes': recipes}
    return render(request, 'admin/moderation_list.html', context) 

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def admin_approve_recipe_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.status != 'pending':
        messages.warning(request, f'Рецепт "{recipe.title}" не находится на модерации.')
    else:
        recipe.status = 'published'
        recipe.moderation_notes = None 
        recipe.save()
        messages.success(request, f'Рецепт "{recipe.title}" одобрен и опубликован!')
    return redirect('admin_moderation_list')


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def admin_reject_recipe_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    
    moderation_notes = request.POST.get('moderation_notes', 'Причина не указана.')
    
    if recipe.status != 'pending':
        messages.warning(request, f'Рецепт "{recipe.title}" не находится на модерации.')
    else:
        recipe.status = 'rejected' 
        recipe.moderation_notes = moderation_notes
        recipe.save()
        messages.info(request, f'Рецепт "{recipe.title}" отклонен и возвращен пользователю как черновик.')
        
    return redirect('admin_moderation_list')

# пользователи
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_detail_view(request, pk):
    user_to_view = get_object_or_404(User, pk=pk)
    total_recipes = user_to_view.recipes.count()
    total_favorites = Favorite.objects.filter(user=user_to_view).count()
    
    context = {
        'profile_user': user_to_view,
        'total_recipes': total_recipes,
        'total_favorites': total_favorites,
    }
    return render(request, 'admin/user_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_edit_view(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, request.FILES, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные пользователя "{user_to_edit.email}" успешно обновлены.')
            return redirect('admin_users_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = AdminUserEditForm(instance=user_to_edit)
        
    context = {
        'form': form,
        'profile_user': user_to_edit,
    }
    return render(request, 'admin/user_edit.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def admin_user_delete_view(request, pk):

    user_to_delete = get_object_or_404(User, pk=pk)

    if user_to_delete == request.user:
        messages.error(request, 'Вы не можете удалить свою учетную запись через эту форму.')
        return redirect('admin_users_list')
        
    email = user_to_delete.email 
    user_to_delete.delete()
    messages.success(request, f'Пользователь "{email}" успешно удален.')
    return redirect('admin_users_list')

# отзывы

@login_required
def recipe_reviews_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    reviews = Review.objects.filter(recipe=recipe).select_related('user').order_by('-created_at') 
    is_author = request.user == recipe.user
    existing_review = None
    user_has_reviewed = False
    
    if request.user.is_authenticated:
        try:
            existing_review = Review.objects.get(recipe=recipe, user=request.user)
            user_has_reviewed = True
        except Review.DoesNotExist:
            pass

    if request.method == 'POST':
        # Валидация: Автор рецепта не может оставлять отзыв
        if is_author:
            messages.error(request, 'Автор рецепта не может оставлять на него отзыв. 🚫')
            return redirect('recipe_reviews', pk=pk) 
        
        # Валидация: Редактирование или создание
        form = ReviewForm(request.POST, instance=existing_review)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.recipe = recipe
            review.user = request.user
            review.save()
            
            messages.success(request, 'Ваш отзыв успешно добавлен/обновлен! 👍')
            return redirect('recipe_reviews', pk=pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме отзыва.')
    else:
        # Для GET-запроса, если отзыв есть, предзаполняем форму
        initial_data = {'rating': existing_review.rating, 'comment': existing_review.comment} if existing_review else {}
        form = ReviewForm(initial=initial_data)

    context = {
        'recipe': recipe,
        'reviews': reviews,
        'form': form,
        'is_author': is_author,
        'user_has_reviewed': user_has_reviewed,
    }
    
    return render(request, 'recipes/recipe_reviews.html', context)