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
from django.core.mail import send_mail
from rest_framework.generics import CreateAPIView, ListAPIView
from django.apps import apps
import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from django.core.mail import EmailMultiAlternatives

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_url = f"{settings.FRONTEND_DOMAIN}/verify-email/{uid}/{token}"

            html_message = render_to_string("emails/verify_email.html", {
                "verify_url": verify_url,
                "user": user,
            })

            send_mail(
                subject="Bitte bestätige deine Registrierung",
                message=f"Klicke hier, um deinen Account zu aktivieren: \n\n{verify_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
            )

            return Response({"message": "Bitte bestätige deine E-Mail-Adresse"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data

        return Response({
            "token": token.key,
            "user": user_data
            })


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logout erfolgreich"}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            User = apps.get_model(settings.AUTH_USER_MODEL)
            user = User.objects.get(pk=uid)

        except (User.DoesNotExist, ValueError, TypeError):
            return HttpResponse("Ungültiger Link", status=400)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return render(request, "verify_success.html")
        else:
            return HttpResponse("Der Bestätigungslink ist ungültig oder abgelaufen", status=400)


class ContactMessageCreateView(CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        logger.debug("Authorization Header:", self.request.headers.get(
            "Authorization"))  # Debugging Log
        instance = serializer.save(user=self.request.user)

        # E-Mail versenden
        send_mail(
            subject=f"Kontaktanfrage von {instance.first_name} {instance.last_name}",
            message=instance.message,
            from_email=instance.email,
            recipient_list=["jsajzew@googlemail.com"],
        )

# Optional: eigene Nachrichten abrufen
class ContactMessageListView(ListAPIView):
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ContactMessage.objects.filter(user=self.request.user).order_by("-timestamp")

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data) 
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "E-Mail erforderlich."}, status=400)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "Wenn die E-Mail existiert, wurde eine Nachricht gesendet"}, status=404)

        token = default_token_generator.make_token(user)
        uid = user.pk
        reset_link = f"{settings.FRONTEND_DOMAIN}/reset-password/{uid}/{token}"

        # HTML-Template rendern
        html_content = render_to_string("emails/password_reset_email.html", {
            "user": user,
            "reset_link": reset_link,
            "year": datetime.now().year,
        })
        text_content = f"Klicke auf diesen Link, um dein Passwort zurückzusetzen: {reset_link}"

        msg = EmailMultiAlternatives(
            subject="Passwort zurücksetzen",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return Response({"message": "E-Mail mit Link zum Zurücksetzen wurde gesendet."})
    
class PasswordResetConfirmView(APIView):
    def post(self, request, uid, token):
        password = request.data.get("password")
        if not password:
            return Response({"error": "Passwort erforderlich."}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=uid)
        except (CustomUser.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Ungültiger Link oder Benutzer nicht gefunden."}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Token ungültig oder abgelaufen."}, status=400)

        user.set_password(password)
        user.save()

        return Response({"message": "Passwort wurde erfolgreich zurückgesetzt."})
    
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class UserContractUploadView(generics.CreateAPIView):
    queryset = UserContract.objects.all()
    serializer_class = UserContractSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class ChatbotContractView(APIView):
    permission_classes = [IsAuthenticated]
    model = SentenceTransformer("all-MiniLM-L6-v2")

    def post(self, request):
        question = request.data.get("question", "").strip()
        if not question:
            return Response({"error": "Keine Frage gestellt."}, status=400)

        try:
            contract = UserContract.objects.get(user=request.user)
        except UserContract.DoesNotExist:
            return Response({"error": "Kein Vertrag gefunden."}, status=404)

        # Text extrahieren und in Absätze aufteilen
        text = contract.text_content or self.extract_text(contract.pdf_file.path)
        paragraphs = self.split_into_paragraphs(text)  # Hier ändern wir zu Absätzen

        # Embeddings für alle Absätze erstellen
        paragraph_embeddings = self.model.encode(paragraphs)
        question_embedding = self.model.encode([question])

        # Ähnlichkeiten berechnen
        scores = cosine_similarity(question_embedding, paragraph_embeddings)[0]
        best_idx = np.argmax(scores)
        best_paragraph = paragraphs[best_idx]

        return Response({"answer": best_paragraph})

    def extract_text(self, path):
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or '' for page in pdf.pages)

    def split_into_paragraphs(self, text):
        """Teilt den Text in logische Absätze auf"""
        # 1. Trennen an zwei oder mehr Zeilenumbrüchen
        raw_paragraphs = re.split(r'\n\s*\n+', text)
        
        # 2. Bereinigen und leere Absätze entfernen
        cleaned_paragraphs = []
        for para in raw_paragraphs:
            cleaned = " ".join(para.split())  # Überflüssige Leerzeichen entfernen
            if cleaned:
                cleaned_paragraphs.append(cleaned)
        
        return cleaned_paragraphs
    
class InsuranceCompanyListView(generics.ListAPIView):
    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer
    permission_classes = [permissions.IsAuthenticated]

class TariffListView(generics.ListAPIView):
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
    serializer_class = CompleteProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


"""
Es ist eine Funktion um DAten aus dem Frontent zu empfangen und im Profil des Users zu speichern
"""
class InsuranceSelectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = InsuranceSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        company_id = data["company"]
        tariff_id = data["tariff"]
        additional_ids = data.get("additional_tariffs", [])

        # Prüfen ob die IDs existieren
        try:
            company = InsuranceCompany.objects.get(id=company_id)
            main_tariff = Tariff.objects.get(id=tariff_id, company=company)
        except InsuranceCompany.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tariff.DoesNotExist:
            return Response({"error": "Tariff not found"}, status=status.HTTP_404_NOT_FOUND)

        # Zusatz-Tarife laden
        additional_tariffs = Tariff.objects.filter(id__in=additional_ids, company=company)

        # Beispiel: speichern beim User (falls du ein Profilmodell hast)
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Prüfen, ob Tarifdaten vorhanden sind
        if not user.insurance_company or not user.tariff:
            return Response({}, status=200)  # leere Response, wenn noch nicht gesetzt

        serializer = MyTariffSerializer(user)  # ModelSerializer erwartet Instanz
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = MyTariffSerializer(user, data=request.data, partial=True)  # partial=True erlaubt optionale Felder
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)