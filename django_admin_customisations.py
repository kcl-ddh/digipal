from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib import admin

# We add more columns to the Admin User list view 

UserAdmin.list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'group_names', 'last_login')
UserAdmin.list_display_links = UserAdmin.list_display
UserAdmin.list_filter += ('groups__name',)
def get_group_names(self, user):
    return ', '.join([u.name for u in user.groups.all()])
get_group_names.short_description = 'Groups'
UserAdmin.group_names = get_group_names

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
