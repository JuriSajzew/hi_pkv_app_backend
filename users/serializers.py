# users/serializers.py
# Serializers for authentication, user profiles, insurance selection
# and related user-facing API endpoints.

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

# Resolve the active user model (supports custom user implementations)
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles user registration and account creation.

    Uses Django's user manager to ensure proper password hashing.
    Newly created users are set inactive to allow email verification.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'phone',
            'street',
            'postal_code',
            'city'
        ]

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

        # Account activation is deferred until verification is completed
        user.is_active = False
        user.save()
        return user


class InsuranceCompanySerializer(serializers.ModelSerializer):
    """
    Minimal serializer for insurance company reference data.
    """
    class Meta:
        model = InsuranceCompany
        fields = ['id', 'name']


class TariffSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for tariffs without nested relations.
    """
    class Meta:
        model = Tariff
        fields = ['id', 'name', 'company', 'type']


class CompleteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer used to complete the insurance-related part
    of a user's profile.
    """
    class Meta:
        model = CustomUser
        fields = ['insurance_company', 'tariff']


class LoginSerializer(serializers.Serializer):
    """
    Authenticates a user using username and password.
    """
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for exposing user profile information to the frontend.
    Field names are adapted to frontend naming conventions.
    """
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
            'profile_completed'
        ]

        def get_profile_completed(self, obj):
            """
            Indicates whether all required profile fields are populated.
            """
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
    """
    Validates password change requests.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class PasswordChangeView(APIView):
    """
    Allows authenticated users to change their password.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Ensure the provided current password is correct
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Incorrect current password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"message": "Password successfully changed"},
            status=status.HTTP_200_OK
        )


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for contact form submissions.
    """
    class Meta:
        model = ContactMessage
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "message",
            "timestamp"
        ]
        read_only_fields = ["id", "timestamp"]


class UserContractSerializer(serializers.ModelSerializer):
    """
    Serializer for user-uploaded contract documents.
    """
    class Meta:
        model = UserContract
        fields = ['user', 'pdf_file']


class TariffSerializer(serializers.ModelSerializer):
    """
    Serializer for tariffs with optional nested add-on tariffs.
    Only main tariffs expose associated additional tariffs.
    """
    additional_tariffs = serializers.SerializerMethodField()

    class Meta:
        model = Tariff
        fields = ["id", "name", "additional_tariffs"]

    def get_additional_tariffs(self, obj):
        if obj.type == "main":
            return [
                {'id': t.id, 'name': t.name}
                for t in obj.additional_tariffs.all()
            ]
        return []


class InsuranceCompanySerializer(serializers.ModelSerializer):
    """
    Serializer for insurance companies including nested main tariffs.
    """
    main_tariffs = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceCompany
        fields = ["id", "name", "main_tariffs"]

    def get_main_tariffs(self, obj):
        main_tariffs = obj.tariffs.filter(type="main")
        return TariffSerializer(main_tariffs, many=True).data


class InsuranceSelectionSerializer(serializers.Serializer):
    """
    Used for submitting insurance and tariff selections from the frontend.
    """
    company = serializers.IntegerField()
    tariff = serializers.IntegerField()
    additional_tariffs = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class MyTariffSerializer(serializers.ModelSerializer):
    """
    Stores and exposes a user's insurance configuration.
    """

    insurance_company = serializers.PrimaryKeyRelatedField(
        queryset=InsuranceCompany.objects.all(),
        write_only=True
    )
    tariff = serializers.PrimaryKeyRelatedField(
        queryset=Tariff.objects.all(),
        write_only=True
    )
    additional_tariffs = serializers.PrimaryKeyRelatedField(
        queryset=Tariff.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    # Read-only helper fields for frontend display
    company_name = serializers.CharField(
        source="insurance_company.name",
        read_only=True
    )
    tariff_name = serializers.CharField(
        source="tariff.name",
        read_only=True
    )
    additional_tariffs_names = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        read_only=True,
        source="additional_tariffs"
    )

    # Optional insurance-related metadata
    insurance_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    monthly_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = [
            "insurance_company",
            "tariff",
            "additional_tariffs",
            "company_name",
            "tariff_name",
            "additional_tariffs_names",
            "insurance_number",
            "monthly_fee"
        ]
