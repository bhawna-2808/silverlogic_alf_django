from django.http import JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import get_user_model
from timed_auth_token.models import TimedAuthToken
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

User = get_user_model()

def switch_user(modeladmin, request, queryset):
    if queryset.count() != 1:
        return JsonResponse({"error": "Please select exactly one user to switch."}, status=400)
    
    user = queryset.first()
    if not user.is_active:
        return JsonResponse({"error": "Cannot switch to an inactive user."}, status=400)

    # Generate or retrieve the token
    token, _ = TimedAuthToken.objects.get_or_create(user=user)

    # Create a new session
    session = SessionStore()
    session.create()
    session['auth_token'] = token.key
    session['switched_user'] = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    session.save()

    # Construct the redirect URL with the session key and token
    redirect_url = f"https://staging.alfcoretrainingflorida.com/#/signin?session_key={session.session_key}&auth_token={token.key}"

    # Prepare additional data
    additional_data = {
        "user_data": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "session_key": session.session_key,
        "auth_token": token.key
    }

    # Return JSON response with the redirect URL and additional data
    return JsonResponse({"redirect_url": redirect_url, "data": additional_data})

switch_user.short_description = "Switch to selected user"

class UserAdmin(DefaultUserAdmin):
    actions = [switch_user]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
