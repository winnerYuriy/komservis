from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django_email_verification import send_email
from .models import Profile, Avatar

User = get_user_model()

from .forms import LoginForm, UserCreateForm, UserUpdateForm


#Register new user
def register_user(request):

    if request.method == 'POST':
        form = UserCreateForm(request.POST)

        if form.is_valid():
            form.save(commit=False)
            user_email=form.cleaned_data.get('email')
            user_username=form.cleaned_data.get('username')
            user_password=form.cleaned_data.get('password1')

            #Create new user
            user = User.objects.create_user(
                username=user_username, email=user_email, password=user_password
            )

            user.is_active = False

            send_email(user)
            
            return redirect('/account/email-verification-sent/')
    else:
        form = UserCreateForm()
    return render(request, 'account/registration/register.html', {'form': form}) 


def login_user(request):

    form = LoginForm()

    if request.user.is_authenticated:
        return redirect('shop:products')

    if request.method == 'POST':

        form = LoginForm(request.POST, request.FILES)

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('account:dashboard')
        else:
            messages.info(request, 'Username or Password is incorrect')
            return redirect('account:login')
    context = {
        'form': form
    }
    return render(request, 'account/login/login.html', context)


def logout_user(request):
    session_keys = list(request.session.keys())
    for key in session_keys:
        if key == 'session_key':
            continue
        del request.session[key]
    logout(request)
    return redirect('shop:products')


@login_required(login_url='account:login')
def dashboard_user(request):
    return render(request, 'account/dashboard/dashboard.html')


@login_required(login_url='account:login')
def profile_user(request):

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect('account:dashboard')
    else:
        form = UserUpdateForm(instance=request.user)

    context = {
        'form': form
    }
        
    return render(request, 'account/dashboard/profile-management.html', context)


@login_required(login_url='account:login')
def delete_user(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        user.delete()
        return redirect('shop:products')
    return render(request, 'account/dashboard/account-delete.html')

@login_required
def select_avatar(request):
    if request.method == 'POST':
        selected_avatar = request.POST.get('avatar')
        request.user.profile.avatar = selected_avatar
        request.user.profile.save()
        return redirect('account:dashboard')
    return render(request, 'account/dashboard/dashboard.html')


@login_required
def update_avatar(request):
    if request.method == 'POST':
        avatar_id = request.POST.get('avatar')
        if avatar_id:
            try:
                avatar = Avatar.objects.get(id=avatar_id)
                request.user.profile.avatar = avatar
                request.user.profile.save()
                return redirect('account:dashboard')
            except Avatar.DoesNotExist:
                # Якщо аватарка не знайдена, можна додати повідомлення про помилку
                pass
    return redirect('account:dashboard')

@login_required
def subscribe(request):
    profile = request.user.profile
    profile.is_subscribed = not profile.is_subscribed  # Перемикаємо стан підписки
    profile.save()
    return redirect('account:dashboard')  # Перенаправлення на кабінет


@login_required
def dashboard_user(request):
    user_profile = request.user.profile  # Отримати профіль користувача
    avatars = Avatar.objects.all()  # Отримати всі доступні аватарки

    context = {
        'user': request.user,
        'avatars': avatars,  # Передати аватарки в контекст
    }

    return render(request, 'account/dashboard/dashboard.html', context)