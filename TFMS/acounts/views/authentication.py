from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from ..forms import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


# Create your views here.
def index(request):
    return render(request, 'index.html')


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to dashboard based on user role
                if user.profile.role == 'farmer':
                    return redirect('farmer_dashboard')
                elif user.profile.role == 'buyer':
                    return redirect('buyer_dashboard')
            else:
                # Invalid login credentials
                return render(request, 'login.html', {'form': form, 'message': 'Invalid username or password'})
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            if User.objects.filter(username=username).exists():
                # User with the same username already exists
                message = "User with the same username already exists."
                return render(request, 'register.html', {'form': form, 'message': message})
            else:
                user = form.save(commit=False)
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()

                profile = Profile.objects.create(
                    user=user,
                    phone=form.cleaned_data['phone'],
                    sex=form.cleaned_data['sex'],
                    role=form.cleaned_data['role'],
                    location=form.cleaned_data['location']
                )
                account = Account.objects.create(
                    user=user,
                    balance=0
                )

                user = authenticate(username=username, password=form.cleaned_data['password1'])
                if user is not None:
                    login(request, user)
                    return redirect('login')  # Redirect to login page after successful registration
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def FarmerDetails(request):
    user = request.user
    profile = Profile.objects.filter(user=user).first()
    if request.method == 'POST':
        form = UserUpdation(request.POST, instance=user)
        former = ProfileForm(request.POST, instance=profile)
        if form.is_valid() and former.is_valid():
            user = form.save()
            profile = former.save(commit=False)
            profile.user = user  # Assign the user instance to the profile
            profile.save()  # Save profile after assigning user
            return redirect('farmer_details')  # Redirect after successful update
    else:
        form = UserUpdation(instance=user)
        former = ProfileForm(instance=profile)
    context = {
        'form': form,
        'former': former,
    }
    return render(request, 'farmer/farmerdetails.html', context)


@login_required(login_url='/login/')
def change_password(request):
    user = request.user
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'change_password.html', {'form': form})


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')

            # Redirect based on user role
            if request.user.profile.role == 'farmer':
                return redirect('farmer_dashboard')
            elif request.user.profile.role == 'buyer':
                return redirect('buyer_dashboard')
            else:
                return redirect('index')  # Fallback redirect if role is not matched
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    # Set the dashboard template based on user's role
    if request.user.profile.role == 'farmer':
        dashboard_template = 'farmer/farmerdashboard.html'
    elif request.user.profile.role == 'buyer':
        dashboard_template = 'buyer/buyerdashboard.html'

    else:
        # Default to member dashboard if role is not recognized
        dashboard_template = 'farmer/farmerdashboard.html'

    return render(request, 'change_password.html', {'form': form, 'dashboard_template': dashboard_template})


@login_required
def update_profile(request):
    user = request.user
    profile = Profile.objects.get(user=user)

    if request.method == 'POST':
        # Get data from the form
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        sex = request.POST.get('sex')
        # role = request.POST.get('role')

        # Update User model
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Update Profile model
        profile.phone = phone
        profile.sex = sex
        # profile.role = role
        profile.save()

        # Redirect to the appropriate dashboard based on role
        if profile.role == 'farmer':
            return redirect('farmer_dashboard')
        elif profile.role == 'buyer':
            return redirect('buyer_dashboard')

    # Set the dashboard template based on user's role
    if profile.role == 'farmer':
        dashboard_template = 'farmer/farmerdashboard.html'
    elif profile.role == 'buyer':
        dashboard_template = 'buyer/buyerdashboard.html'
    else:
        # Default to member dashboard if role is not recognized
        dashboard_template = 'farmer/farmerdashboard.html'

    context = {
        'user': user,
        'profile': profile,
        'dashboard_template': dashboard_template,
    }

    # Add a success message
    messages.success(request, 'Your profile has been successfully updated!')

    return render(request, 'update_profile.html', context)