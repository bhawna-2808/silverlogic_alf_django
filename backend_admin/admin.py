from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.http import JsonResponse
from django.contrib import messages
from timed_auth_token.models import TimedAuthToken
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()

def switch_user(modeladmin, request, queryset):
    if queryset.count() != 1:
        # Ensure exactly one user is selected
        messages.error(request, "Please select exactly one user to switch.")
        return JsonResponse({"error": "Please select exactly one user to switch."}, status=400)
    
    user = queryset.first()

    if not user.is_active:
        # Check if the user is active
        messages.error(request, "Cannot switch to an inactive user.")
        return JsonResponse({"error": "Cannot switch to an inactive user."}, status=400)

    # Generate or retrieve the token for the user
    token, _ = TimedAuthToken.objects.get_or_create(user=user)

    # Create a new session for the user switch
    session = SessionStore()
    session.create()

    # Store the token and user data in the new session
    session['auth_token'] = token.key
    session['switched_user'] = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    session.save()

    # Construct the redirect URL with the session key and token
    redirect_url = f"https://staging.alfcoretrainingflorida.com/#/facility?session_key={session.session_key}&auth_token={token.key}"

    messages.success(request, f"Switched to user: {user.username}")

    # Return a JSON response with redirect URL and token details
    response_data = {
        "redirect_url": redirect_url,
        "auth_token": token.key,
        "session_key": session.session_key,
        "user": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    }
    return JsonResponse(response_data)

switch_user.short_description = "Switch to selected user"

class UserAdmin(DefaultUserAdmin):
    actions = [switch_user]

# Unregister the default User model and register the customized one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
