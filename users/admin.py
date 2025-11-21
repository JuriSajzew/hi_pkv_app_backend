# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserContract, InsuranceCompany, Tariff


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ("Zusätzliche Infos", {
            "fields": (
                "phone",
                "street",
                "postal_code",
                "city",
                "insurance_company",
                "tariff",
                "additional_tariffs",
                "insurance_number",
                "monthly_fee",
                "profile_completed",
            ),
        }),
    )
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'type')
    search_fields = ('name', 'company__name')
    list_filter = ('type', 'company')

@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserContract)
class UserContractAdmin(admin.ModelAdmin):
    list_display = ('user', 'pdf_file')
    search_fields = ('user__username', 'user__email')

