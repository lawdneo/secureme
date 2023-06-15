import datetime
import hashlib
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from users.emails import send_reset_email, send_validation_email
from users.models import (
    ApprovalRequests,
    CustomUser,
    PasswordReset,
    Station,
    ValidationEmailCodes,
)
from users.serializers import UserSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# Create your views here.
USER_MODEL = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    password1 = request.data.get("password1")
    password2 = request.data.get("password2")
    email = request.data.get("email")
    username = request.data.get("username")

    if username == None or password1 == None or password2 == None or email == None:
        return Response({"error": "Fill in all required fields"}, status=400)

    if password1 != password2:
        return Response({"error": "Passwords do not match"}, status=400)
    else:
        try:
            user = USER_MODEL.objects.get(email=email)
            return Response({"error": "User already exists"}, status=400)
        except USER_MODEL.DoesNotExist:
            user = USER_MODEL.objects.create(email=email, username=username)
            user.set_password(password1)
            user.is_active = False
            user.save()
            send_validation_email(user)
            return Response(
                {
                    "message": "User Registration successful. An email has been sent to activate your account"
                },
                status=201,
            )

@api_view(["POST"])
def validate_email_activate_account(request):
    if "code" in request.data and "email" in request.data:
        user = get_object_or_404(USER_MODEL, email=request.data.get("email"))
        if user.is_active:
            return Response({"error:": "Account is already active"}, status=status.HTTP_400_BAD_REQUEST)
        time_threshold = datetime.now() - timedelta(minutes=14)
        code = request.data.get("code")
        validation_codes = ValidationEmailCodes.objects.filter(
            user=user, date_requested__gt=time_threshold,code_used=False
        )
        validation_code = validation_codes.latest("date_requested")
        if str(code) == str(validation_code.code):
            user.is_active = True
            validation_code.code_used = True
            validation_code.save()
            user.save()
            return Response({"message":"Account Activated successfully"}, status=200)
        else:
            return Response({"error": f"Incorrect Code entered "}, status=400)
    else:
        return Response({"error":"Fill in all required fields"},status=400)

@api_view(["POST"])
def resend_validation_email(request):
    if "email" in request.data:
        user = get_object_or_404(USER_MODEL, email=request.data.get("email"))
        if user.is_active:
            return Response({"error:": "Account is already active"}, status=status.HTTP_400_BAD_REQUEST)
        if send_validation_email(user):
            return Response(
                {"message": "Email sent successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "An error has occured"}, status=status.HTTP_502_BAD_GATEWAY
            )

    else:
        return Response(
            {"error": "Email field is required"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)

    if user is not None:
        if user.approved:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "message": "Login successful.",
                    "token": token.key,
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Your account is not approved."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    else:
        return Response(
            {"error": "Invalid login credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(["POST"])
def approval_request_view(request):
    user_email = request.data.get("email")
    station = request.data.get("station")

    if user_email is None or station is None:
        return Response(
            {"error": "Please provide email and station."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = CustomUser.objects.get(email=user_email)
    station = Station.objects.get(id=station)

    if user is not None:
        if user.approved:
            return Response(
                {"error": "User is already approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {"error": "User approval is pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        approval_request = ApprovalRequests.objects.create(user=user, station=station)
        return Response(
            {
                "message": "The user has been approved",
                "approval": {"id": approval_request.id},
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_email(request):
    if "email" in request.data:
        email = request.data.get("email")
        user = get_object_or_404(USER_MODEL, email=email)

        if send_reset_email(user):
            return Response(
                {"message": "Email sent successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "An error has occured"}, status=status.HTTP_502_BAD_GATEWAY
            )

    else:
        return Response(
            {"error": "Email field is required"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_reset_code(request):
    if "code" in request.data:
        user = get_object_or_404(USER_MODEL, email=request.data.get("email"))
        time_threshold = datetime.now() - timedelta(minutes=14)
        code = request.data.get("code")
        password_resets = PasswordReset.objects.filter(
            user=user, date_requested__gt=time_threshold, code_used=False
        )
        password_reset = password_resets.latest("date_requested")
        if str(code) == str(password_reset.reset_code):
            to_encode: str = (
                request.data.get("email")
                + str(code)
                + str(int(datetime.now().timestamp()))
            )
            grant_token = hashlib.md5(to_encode.encode()).hexdigest()
            password_reset.grant_token = grant_token
            password_reset.is_valid = True
            password_reset.save()
            return Response({"grant_token": grant_token}, status=200)
        else:
            return Response(f"Incorrect Code", status=400)
    else:
        return Response(status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request, grant_token):
    if "password1" in request.data and "password2" in request.data:
        time_threshold = datetime.now() - timedelta(minutes=14)

        pass_request = get_object_or_404(
            PasswordReset,
            grant_token=grant_token,
            is_valid=True,
            date_requested__gt=time_threshold,
            code_used=False,
        )
        user = pass_request.user
        pass1 = request.data.get("password1")
        pass2 = request.data.get("password2")
        if pass1 == pass2:
            user.set_password(pass1)
            pass_request.code_used = True
            pass_request.save()
            user.save()
            return Response({"message": "Password reset successful"}, status=200)
        else:
            return Response({"error": "Passwords do not match"}, status=400)
    else:
        return Response({"error": "Some fields are missing"}, status=400)
