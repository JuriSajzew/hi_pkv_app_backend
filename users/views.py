from datetime import datetime
from rest_framework import generics, status, permissions
from django.template.loader import render_to_string
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from users.models import ContactMessage, CustomUser, UserContract, InsuranceCompany, Tariff
from .serializers import CompleteProfileSerializer, ContactMessageSerializer, InsuranceCompanySerializer, InsuranceSelectionSerializer, MyTariffSerializer, RegisterSerializer, LoginSerializer, TariffSerializer, UserContractSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from rest_framework.generics import CreateAPIView, ListAPIView
from django.apps import apps
import pdfplumber
import logging
from users.services.mail import send_contact_mail
from django.shortcuts import render

# Module-level logger for error tracking and operational visibility
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    Handles user registration and triggers email verification.

    Creates an inactive user account and sends a verification email
    containing a tokenized activation link.
    """

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Encode user ID and generate a one-time verification token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Resolve frontend domain for activation link generation
            frontend_domain = getattr(settings, "FRONTEND_DOMAIN", "http://localhost:3000")

            verify_url = f"{frontend_domain}/api/users/verify-email/{uid}/{token}/"

            try:
                # Render HTML email template
                html_message = render_to_string(
                    "emails/verify_email.html",
                    {
                        "verify_url": verify_url,
                        "user": user,
                    },
                )

                # Send verification email
                send_mail(
                    subject="Bitte bestätige deine Registrierung",
                    message=f"Klicke hier, um deinen Account zu aktivieren: \n\n{verify_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                )
            except Exception as e:
                # Email failures must never crash the application container
                logger.error(f"Registrierungs-Mail konnte nicht gesendet werden: {e}")

            return Response(
                {"message": "Bitte bestätige deine E-Mail-Adresse"},
                status=status.HTTP_201_CREATED
            )


class LoginView(APIView):
    """
    Authenticates a user and issues a token for API access.
    """
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Serializer returns the authenticated user instance
        user = serializer.validated_data

        # Create or reuse authentication token
        token, _ = Token.objects.get_or_create(user=user)

        # Serialize user data for frontend consumption
        user_data = UserSerializer(user).data

        return Response({
            "token": token.key,
            "user": user_data
        })


class LogoutView(APIView):
    """
    Invalidates the current authentication token.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {"message": "Logout erfolgreich"},
            status=status.HTTP_200_OK
        )


class VerifyEmailView(APIView):
    """
    Activates a user account after successful email verification.
    """

    def get(self, request, uidb64, token):
        try:
            # Decode user ID from URL-safe base64
            uid = force_str(urlsafe_base64_decode(uidb64))
            User = apps.get_model(settings.AUTH_USER_MODEL)
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return HttpResponse("Ungültiger Link", status=400)

        # Validate token and activate account
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return render(request, "verify_success.html")
        else:
            return HttpResponse(
                "Der Bestätigungslink ist ungültig oder abgelaufen",
                status=400
            )


class ContactMessageCreateView(CreateAPIView):
    """
    Allows authenticated users to submit contact messages.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Attach message to the authenticated user and send notification email
        instance = serializer.save(user=self.request.user)
        send_contact_mail(instance)


class ContactMessageListView(ListAPIView):
    """
    Returns all contact messages of the authenticated user.
    """
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ContactMessage.objects.filter(
            user=self.request.user
        ).order_by("-timestamp")


class UserDetailView(APIView):
    """
    Retrieve or update the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class IsAdmin(permissions.BasePermission):
    """
    Custom permission allowing access only to staff users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class UserContractUploadView(generics.CreateAPIView):
    """
    Allows administrators to upload contract documents for users.
    """
    queryset = UserContract.objects.all()
    serializer_class = UserContractSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class InsuranceCompanyListView(generics.ListAPIView):
    """
    Returns a list of all insurance companies.
    """
    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer
    permission_classes = [permissions.IsAuthenticated]


class TariffListView(generics.ListAPIView):
    """
    Returns tariffs filtered by insurance company and/or tariff type.
    """
    serializer_class = TariffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company_id = self.request.query_params.get('company')
        tariff_type = self.request.query_params.get('type')

        queryset = Tariff.objects.all()

        if company_id:
            queryset = queryset.filter(company_id=company_id)

        if tariff_type:
            queryset = queryset.filter(type=tariff_type)

        return queryset


class CompleteProfileView(generics.UpdateAPIView):
    """
    Completes the insurance profile of the authenticated user.
    """
    serializer_class = CompleteProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class InsuranceSelectionView(APIView):
    """
    Receives insurance selections from the frontend
    and persists them in the user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = InsuranceSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        company_id = data["company"]
        tariff_id = data["tariff"]
        additional_ids = data.get("additional_tariffs", [])

        # Validate referenced insurance company and tariff
        try:
            company = InsuranceCompany.objects.get(id=company_id)
            main_tariff = Tariff.objects.get(id=tariff_id, company=company)
        except InsuranceCompany.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tariff.DoesNotExist:
            return Response({"error": "Tariff not found"}, status=status.HTTP_404_NOT_FOUND)

        # Load optional add-on tariffs
        additional_tariffs = Tariff.objects.filter(
            id__in=additional_ids,
            company=company
        )

        # Persist insurance selection in user profile
        user = request.user
        user.insurance_company = company
        user.tariff = main_tariff
        user.additional_tariffs.set(additional_tariffs)
        user.profile_completed = True
        user.save()

        return Response({
            "message": "Insurance selection saved",
            "company": company.name,
            "tariff": main_tariff.name,
            "additional_tariffs": [t.name for t in additional_tariffs],
        }, status=status.HTTP_200_OK)


class MyTariffView(APIView):
    """
    Retrieve or update the authenticated user's insurance data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Return empty response if insurance data is not yet set
        if not user.insurance_company or not user.tariff:
            return Response({}, status=200)

        serializer = MyTariffSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = MyTariffSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def get_user_by_email(email):
    """
    Retrieve a user by email address.
    Returns None if the user does not exist.
    """
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return None


def build_reset_link(user):
    """
    Generate a secure password reset link for a user.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_DOMAIN}/api/users/reset-password/{uidb64}/{token}"


def render_reset_email(user, reset_link):
    """
    Render password reset email content (plain text and HTML).
    """
    html = render_to_string(
        "emails/password_reset_email.html",
        {"user": user, "reset_link": reset_link, "year": datetime.now().year},
    )
    text = f"Klicke auf diesen Link, um dein Passwort zurückzusetzen: {reset_link}"
    return text, html


def send_reset_email(email, text, html):
    """
    Send password reset email using multipart (text + HTML).
    """
    msg = EmailMultiAlternatives(
        subject="Passwort zurücksetzen",
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def get_user_from_uid(uid):
    """
    Resolve a user instance from a base64-encoded UID.
    """
    try:
        decoded_uid = force_str(urlsafe_base64_decode(uid))
        return CustomUser.objects.get(pk=decoded_uid)
    except (CustomUser.DoesNotExist, ValueError, TypeError):
        return None


def validate_token(user, token):
    """
    Validate a password reset token for the given user.
    """
    return default_token_generator.check_token(user, token)


class PasswordResetRequestView(APIView):
    """
    Initiates the password reset process.
    """
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "E-Mail erforderlich."}, status=400)

        user = get_user_by_email(email)
        if user:
            link = build_reset_link(user)
            text, html = render_reset_email(user, link)
            send_reset_email(email, text, html)

        return Response(
            {"message": "Wenn die E-Mail existiert, wurde eine Nachricht gesendet."},
            status=200,
        )


class PasswordResetConfirmView(APIView):
    """
    GET: Displays the password reset form.
    POST: Validates and stores the new password.
    """

    def get(self, request, uid, token):
        user = get_user_from_uid(uid)

        if not user or not validate_token(user, token):
            return render(request, "emails/password_reset_invalid.html")

        return render(request, "emails/password_reset_confirm.html")

    def post(self, request, uid, token):
        user = get_user_from_uid(uid)

        if not user or not validate_token(user, token):
            return render(request, "emails/password_reset_invalid.html")

        # Extract password depending on request content type
        if request.content_type == "application/json":
            password = request.data.get("password")
            password_confirm = request.data.get("password_confirm", password)
        else:
            password = request.POST.get("password")
            password_confirm = request.POST.get("password_confirm")

        # Validate password input
        if not password:
            return render(
                request,
                "emails/password_reset_confirm.html",
                {"error": "Bitte gib ein Passwort ein."}
            )

        if len(password) < 8:
            return render(
                request,
                "emails/password_reset_confirm.html",
                {"error": "Das Passwort muss mindestens 8 Zeichen lang sein."}
            )

        if password != password_confirm:
            return render(
                request,
                "emails/password_reset_confirm.html",
                {"error": "Die Passwörter stimmen nicht überein."}
            )

        if user.check_password(password):
            return render(
                request,
                "emails/password_reset_confirm.html",
                {"error": "Das neue Passwort darf nicht mit dem alten Passwort übereinstimmen."}
            )

        # Persist new password
        user.set_password(password)
        user.save(update_fields=["password"])

        return render(request, "emails/password_reset_success.html")
