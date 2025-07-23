import pytest
import os
import sys
import django
import base64
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from api.models import User

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append('E:/programming/React-Django-Project/SZKblog/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

@pytest.mark.django_db
class TestPasswordReset:
    def setup_method(self):
        self.client = APIClient()
        User.objects.filter(username="testuser").delete()
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="oldpassword123")

    def test_password_email_verify(self):
        url = reverse('password-email-verify', kwargs={'email': self.user.email})
        response = self.client.get(url)
        assert response.status_code == 200
        user = User.objects.get(email=self.user.email)
        assert user.otp != ""
        assert user.reset_token != ""

    def test_password_change_success(self):
        # First get otp and reset_token
        url_verify = reverse('password-email-verify', kwargs={'email': self.user.email})
        self.client.get(url_verify)
        user = User.objects.get(email=self.user.email)
        uidb64 = base64.urlsafe_b64encode(str(user.pk).encode()).decode()
        payload = {
            "otp": user.otp,
            "uidb64": uidb64,
            "reset_token": user.reset_token,
            "password": "newpassword123"
        }
        url_change = reverse('password-change')
        response = self.client.post(url_change, data=payload, format='json')
        assert response.status_code == 201
        user.refresh_from_db()
        assert user.check_password("newpassword123")
        assert user.otp == ""
        assert user.reset_token == ""

    def test_password_change_invalid_token(self):
        uidb64 = base64.urlsafe_b64encode(str(self.user.pk).encode()).decode()
        payload = {
            "otp": "wrongotp",
            "uidb64": uidb64,
            "reset_token": "wrongtoken",
            "password": "newpassword123"
        }
        url_change = reverse('password-change')
        response = self.client.post(url_change, data=payload, format='json')
        assert response.status_code == 400
        assert response.data["message"] == "Invalid token or OTP"
