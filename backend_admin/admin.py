import requests
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from urllib.parse import urlencode
from timed_auth_token.models import TimedAuthToken  # Import your token model

# Get the default User model
User = get_user_model()

# Define the switch user action
def switch_user(modeladmin, request, queryset):
    if queryset.count() == 1:
        user = queryset.first()
        
        # Ensure the user is active before switching
        if not user.is_active:
            messages.error(request, "Cannot switch to an inactive user.")
            return
        
        # Generate or retrieve the token
        token, created = TimedAuthToken.objects.get_or_create(user=user)
        
        # Get the current host from the request object
        current_host = request.get_host()
        
        # Construct the dynamic login API URL
        login_api_url = f"https://{current_host}/api/login/"
        
        # Call the login API with the token
        response = requests.post(login_api_url, data={'token': token.key})

        if response.status_code == 200:
            # Prepare user data to send in URL if required
            user_data = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'token': token.key
            }
            
            # Encode the user data
            # encoded_data = urlencode(user_data)
            
            # Construct the redirect URL
            # redirect_url = f"https://staging.alfcoretrainingflorida.com/#/facility?{encoded_data}"
            
            messages.success(request, f"Switched to user: {user.username}")
            # return HttpResponseRedirect(redirect_url)
        else:
            messages.error(request, "Login failed. Please try again.")
            
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
    
    else:
        messages.error(request, "Please select exactly one user to switch.")
        return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

switch_user.short_description = "Switch to selected user"

# Create a custom UserAdmin class
class UserAdmin(DefaultUserAdmin):
    actions = [switch_user]

# Unregister the default User admin and re-register it with custom UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

