from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User  # Import the User model correctly
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model
from apps.facilities.models import FacilityUser  # Adjusted import based on app folder structure
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import UserForm
from django.db import transaction


def login(request):  # Rename the view to avoid conflict with login function
    try:
        if request.user.is_authenticated:
            return redirect("dashboard")

        if request.method == "POST":
            username_or_email = request.POST.get("username_or_email")
            # email = request.POST.get("email")
            password = request.POST.get("password")

            # Fetch user by email
            try:
                user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))

                # user = User.objects.get(email=email)  # Correct model reference
            except User.DoesNotExist:
                messages.error(request, "Invalid email or password!")
                return redirect("login")

            # Authenticate using the user's username
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                auth_login(request, user)  # Use auth_login to avoid conflicts
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid email or password!")
                return redirect("login")

        return render(request, "backend_ui/login.html")
    
    except Exception as ex:
        print("Error in login_view:", ex)
        # messages.error(request, "An error occurred. Please try again.")
        return redirect("login")


@login_required
def dashboard(request):
    return render(request, "backend_ui/dashboard.html")


@login_required
def user_logout(request):
    logout(request)
    return redirect("login")



def user_list(request):
    User = get_user_model()  # Ensure correct call to get_user_model()
    print (User)
    users = User.objects.all()  
    print(users)  
    # Fetch FacilityUser data for each user
    facility_users = FacilityUser.objects.select_related('user', 'facility').all()
    return render(
        request,
        "backend_ui/user/user_list.html",
        {
            "users": users,  # Pass regular users
            "facility_users": facility_users,  # Pass facility users
        },
    )


def delete_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    
    try:
        # Use a transaction to ensure both user and facility user are deleted together
        with transaction.atomic():
            # Delete the associated FacilityUser record if it exists
            FacilityUser.objects.filter(user=user).delete()
            
            # Delete the user
            user.delete()
        
        messages.success(request, f"User {user.username} and related facility data deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting user: {str(e)}")

    # Redirect to the user list after deletion
    return redirect(reverse('user_list'))

def edit_user(request,id):
    User = get_user_model()
    instance = get_object_or_404(User, id=id)
    form = UserForm(
        request.POST or None, request.FILES or None, instance=instance
    )
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("user_list")

        else:
            return render(
                request,
                "backend_ui/user/edit_user.html",
                {"form": form, "title": "Update User"},
            )
    return render(
        request,
        "backend_ui/user/edit_user.html",
        {"form": form, "title": "Update User"},
    )


    