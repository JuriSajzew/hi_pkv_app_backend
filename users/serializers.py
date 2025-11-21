# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from users.models import ContactMessage, CustomUser, UserContract, Tariff, InsuranceCompany
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name',
                  'last_name', 'phone', 'street', 'postal_code', 'city']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            street=validated_data['street'],
            postal_code=validated_data['postal_code'],
            city=validated_data['city'],
        )
        user.is_active = False  # Email-Verifizierung
        user.save()
        return user

class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = ['id', 'name']

class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ['id', 'name', 'company', 'type']

class CompleteProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['insurance_company', 'tariff']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

class UserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')

    class Meta:
        model = User
        fields = [
            'firstName', 
            'lastName', 
            'email', 
            'phone', 
            'street', 
            'postal_code', 
            'city',
            'insurance_company',
            'tariff',
            'profile_completed']
        
        def get_profile_completed(self, obj):
        # Prüfen, ob alle Felder gesetzt sind
            required_fields = [
                obj.first_name,
                obj.last_name,
                obj.email,
                obj.phone,
                obj.street,
                obj.postal_code,
                obj.city,
                obj.insurance_company,
                obj.tariff
            ]
            return all(required_fields)

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class PasswordChangeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"error": "Falsches aktuelles Passwort"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Passwort erfolgreich geändert"}, status=status.HTTP_200_OK)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "user", "first_name",
                  "last_name", "email", "message", "timestamp"]
        read_only_fields = ["user", "timestamp"]


class UserContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContract
        fields = ['user', 'pdf_file'] 
        
"""
Tariff Serializer für verschachtelte Darstellung in InsuranceCompanySerializer
"""
class TariffSerializer(serializers.ModelSerializer):
    additional_tariffs = serializers.SerializerMethodField()

    class Meta:
        model = Tariff
        fields = ["id", "name", "additional_tariffs"]

    def get_additional_tariffs(self, obj):
        if obj.type == "main":
            # gibt nur Zusatz-Tarife für diesen Haupttarif zurück
            return [{'id': t.id, 'name': t.name} for t in obj.additional_tariffs.all()]
        return []
    
"""
InsuranceCompany Serializer mit verschachtelten Tariffs
"""

class InsuranceCompanySerializer(serializers.ModelSerializer):
    main_tariffs = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceCompany
        fields = ["id", "name", "main_tariffs"]

    def get_main_tariffs(self, obj):
        main_tariffs = obj.tariffs.filter(type="main")
        return TariffSerializer(main_tariffs, many=True).data

"""
InsuranceSelection Serializer für die Auswahl der Versicherung im Frontend
"""   
class InsuranceSelectionSerializer(serializers.Serializer):
    company = serializers.IntegerField()
    tariff = serializers.IntegerField()
    additional_tariffs = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

"""
Serializer für User-Profil mit Versicherungsdaten
"""
class MyTariffSerializer(serializers.ModelSerializer):
    insurance_company = serializers.PrimaryKeyRelatedField(
        queryset=InsuranceCompany.objects.all(), write_only=True
    )
    tariff = serializers.PrimaryKeyRelatedField(
        queryset=Tariff.objects.all(), write_only=True
    )
    additional_tariffs = serializers.PrimaryKeyRelatedField(
        queryset=Tariff.objects.all(), many=True, write_only=True, required=False
    )

    # Optional: Namen der Auswahl zur Anzeige im Frontend
    company_name = serializers.CharField(source="insurance_company.name", read_only=True)
    tariff_name = serializers.CharField(source="tariff.name", read_only=True)
    additional_tariffs_names = serializers.SlugRelatedField(
        many=True, slug_field="name", read_only=True, source="additional_tariffs"
    )

    # Weitere Profilfelder
    insurance_number = serializers.CharField(required=False, allow_blank=True)
    monthly_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            "insurance_company", "tariff", "additional_tariffs",
            "company_name", "tariff_name", "additional_tariffs_names",
            "insurance_number", "monthly_fee"
        ]