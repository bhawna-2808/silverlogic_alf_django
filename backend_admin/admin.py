from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse

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
        
        # Log in as the selected user
        # login(request, user)
        # Log in as the selected user, even if they don't have staff status

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Redirect to the home page or any specific page
        messages.success(request, f"Switched to user: {user.username}")
        return HttpResponseRedirect(reverse('dashboard'))

        
    else:
        messages.error(request, "Please select exactly one user to switch.")
        return

switch_user.short_description = "Switch to selected user"

# Create a custom UserAdmin class
class UserAdmin(DefaultUserAdmin):
    actions = [switch_user]  # Add the switch user action

# Unregister the default User admin and re-register it with custom UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
