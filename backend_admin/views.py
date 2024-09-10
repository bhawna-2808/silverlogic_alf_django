from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User  # Import the User model correctly
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model
from apps.facilities.models import FacilityUser  # Adjusted import based on app folder structure



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
