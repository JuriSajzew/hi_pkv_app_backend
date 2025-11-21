from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

class InsuranceCompany(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Tariff(models.Model):
    TARIFF_TYPE_CHOICES = (
        ('main', 'Haupttarif'),
        ('additional', 'Zusatzversicherung'),
    )

    name = models.CharField(max_length=100)
    company = models.ForeignKey(InsuranceCompany, related_name="tariffs", on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TARIFF_TYPE_CHOICES, default='main')
    additional_tariffs = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='main_tariffs_set',
        limit_choices_to={'type': 'additional'}
    )

    def __str__(self):
        return f"{self.name} ({self.company.name}, {self.type})"

class ContactMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_messages"
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} ({self.user.username})"


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)

    insurance_company = models.ForeignKey(InsuranceCompany, null=True, blank=True, on_delete=models.SET_NULL)
    tariff = models.ForeignKey(Tariff, null=True, blank=True, on_delete=models.SET_NULL)
    additional_tariffs = models.ManyToManyField(Tariff, blank=True, related_name="users_additional_tariffs")
    insurance_number = models.CharField(max_length=100, null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    profile_completed = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name',
                       'phone', 'street', 'postal_code', 'city']

class UserContract(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contract'
    )
    pdf_file = models.FileField(upload_to='')
    text_content = models.TextField(blank=True)

    def __str__(self):
        return f"Contract for {self.user.username}" 
    
