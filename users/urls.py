from django.urls import path

from users.serializers import PasswordChangeView
from .views import CompleteProfileView, InsuranceCompanyListView, InsuranceSelectionView, MyTariffView, TariffListView, VerifyEmailView, RegisterView, ContactMessageCreateView, ContactMessageListView, LogoutView, PasswordResetConfirmView, PasswordResetRequestView, RegisterView, LoginView, UserDetailView
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('verify-email/<uidb64>/<token>/',
         VerifyEmailView.as_view(), name='verify-email'),

    path("contact/", ContactMessageCreateView.as_view(), name="contact-create"),
    path("contact/messages/", ContactMessageListView.as_view(), name="contact-list"),
    path('users-detail/', UserDetailView.as_view(), name='user-detail'),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("reset-password/<uid>/<token>/", PasswordResetConfirmView.as_view()),
    path('insurance-companies/', InsuranceCompanyListView.as_view(), name='insurance-companies'),
    path('tariffs/', TariffListView.as_view(), name='tariffs'),
    path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    path("insurance-selection/", InsuranceSelectionView.as_view(), name="insurance-selection"),
    path("my-tariff/", MyTariffView.as_view(), name="my-tariff"),
]
