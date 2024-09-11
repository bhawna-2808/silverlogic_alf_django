from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from timed_auth_token.models import TimedAuthToken
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

User = get_user_model()

def switch_user(modeladmin, request, queryset):
    if queryset.count() == 1:
        user = queryset.first()
        
        if not user.is_active:
            messages.error(request, "Cannot switch to an inactive user.")
            return
        
        # Generate or retrieve the token
        token, created = TimedAuthToken.objects.get_or_create(user=user)
        
        # Create a new session
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
        
        # Construct the URL with the session key
        redirect_url = f"https://staging.alfcoretrainingflorida.com/#/signin?session_key={session.session_key}"
        
        messages.success(request, f"Switched to user: {user.username}")
        return HttpResponseRedirect(redirect_url)
    else:
        messages.error(request, "Please select exactly one user to switch.")
        return

switch_user.short_description = "Switch to selected user"

class UserAdmin(DefaultUserAdmin):
    actions = [switch_user]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)