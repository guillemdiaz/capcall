from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import Fund, Investor, Subscription

admin.site.register(Fund)
admin.site.register(Subscription)


class InvestorAdmin(UserAdmin):
    # Add User
    add_fieldsets = (UserAdmin.add_fieldsets or ()) + (
        ("Investor Profile", {"fields": ("investor_type", "kyc_status", "country")}),
    )

    # Change User
    fieldsets = (UserAdmin.fieldsets or ()) + (
        ("Investor Profile", {"fields": ("investor_type", "kyc_status", "country")}),
    )

    # Columns in the general list
    list_display = ["username", "email", "investor_type", "kyc_status", "is_staff"]


admin.site.register(Investor, InvestorAdmin)
