from django.contrib.auth import authenticate, login as auth_login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login(request):
    try:
        if request.user.is_authenticated:
            return redirect("dashboard")
        if request.method == "POST":
            email = request.POST["email"]
            password = request.POST["password"]

            # Fetch user by email
            try:
                user = user.objects.get(email=email)
                email = user.email
            except user.DoesNotExist:
                messages.error(request, "Invalid email or password!")
                return redirect("index")

            user = authenticate(request, email=email, password=password)
            print(user)
            if user is not None:
                login(request, user)
                # messages.success(request, "Welcome to the Dashboard!")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid email or password!")
                return redirect("index")
        return render(request, "backend_ui/login.html")
    except Exception as ex:
        print("Error in: login_page method", ex)
        messages.error(request, "An error occurred. Please try again.")
    return render(request, "backend_ui/login.html")




def dashboard(request):
    return render(request, "backend_ui/dashboard.html")

@login_required
def user_logout(request):
    logout(request)
    return redirect("login")