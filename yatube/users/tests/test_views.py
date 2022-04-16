from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersViewsTests.user)

    def test_users_views_use_correct_template(self):
        """View использует соответствующий шаблон."""
        namespaces_templates = {
            'signup': 'users/signup.html',
            'login': 'users/login.html',
            'password_change_form': 'users/password_change_form.html',
            'password_change_done': 'users/password_change_done.html',
            'password_reset_form': 'users/password_reset_form.html',
            'password_reset_done': 'users/password_reset_done.html',
            'password_reset_complete': 'users/password_reset_complete.html',
            'logout': 'users/logged_out.html',
        }
        for namespace, template in namespaces_templates.items():
            with self.subTest(namespace=namespace):
                response = self.authorized_client.get(
                    reverse('users:' + namespace)
                )
                self.assertTemplateUsed(response, template)

    def test_users_view_password_reset_confirm_use_correct_template(self):
        response = self.authorized_client.get(
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': 'uidb64', 'token': 'token'})
        )
        self.assertTemplateUsed(response, 'users/password_reset_confirm.html')

    def test_users_signup_show_correct_context(self):
        """Шаблон users_signup сформированы с правильной формой из контекста"""
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        response = self.authorized_client.get(reverse('users:signup'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
