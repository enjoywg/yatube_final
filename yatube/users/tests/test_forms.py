from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersSignupFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_users_signup_form(self):
        """Валидная форма создает юзера"""
        form_data = {
            'first_name': 'Тест',
            'last_name': 'Тестович',
            'username': 'test_user',
            'email': 'test@test.com',
            'password1': 'vfdfvdvfdFD',
            'password2': 'vfdfvdvfdFD',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(
            User.objects.filter(
                username='test_user',
                first_name='Тест',
                last_name='Тестович',
                email='test@test.com',
            ).exists()
        )
