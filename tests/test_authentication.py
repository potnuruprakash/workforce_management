"""
Automated tests for authentication, sessions, and access control.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.organizations.models import Organization
from apps.accounts.models import OrganizationMembership, Role


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password123',
            email='test@workforce.local'
        )
        self.org = Organization.objects.create(
            name="Test Org",
            organization_type=Organization.TYPE_COMPANY,
            email="info@test.com",
            phone="1234567890",
            address="Test Address"
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role=Role.EMPLOYEE,
            is_default=True
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated requests to protected views should be redirected to login."""
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_valid_login(self):
        """User can sign in successfully with valid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_invalid_login_shows_error(self):
        """Invalid credentials show error and remain on login page."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_logout(self):
        """Logout terminates the session safely."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))
