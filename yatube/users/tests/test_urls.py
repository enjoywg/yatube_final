from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
            password='hfdsvnvfkn@nkvF',
            email='vdfvfd@dfvfg.com'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_users_urls_http_answer(self):
        """URL-адрес дает корректный ответ"""
        url_answers = {
            'signup/': 'OK',
            'login/': 'OK',
            'password_change/': 'OK',
            'password_change/done/': 'OK',
            'password_reset/': 'OK',
            'password_reset/done/': 'OK',
            'reset/<uidb64>/<token>/': 'OK',
            'reset/done/': 'OK',
            'no/done1211/': 'Not Found',
            'logout/': 'OK',
        }
        for address, answer in url_answers.items():
            with self.subTest(address=address):
                response = self.authorized_client.get('/auth/' + address)
                self.assertEqual(response.reason_phrase, answer)

    def test_users_urls_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            'signup/': 'users/signup.html',
            'login/': 'users/login.html',
            'password_change/': 'users/password_change_form.html',
            'password_change/done/': 'users/password_change_done.html',
            'password_reset/': 'users/password_reset_form.html',
            'password_reset/done/': 'users/password_reset_done.html',
            'reset/<uidb64>/<token>/': 'users/password_reset_confirm.html',
            'reset/done/': 'users/password_reset_complete.html',
            'logout/': 'users/logged_out.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get('/auth/' + address)
                self.assertTemplateUsed(response, template)
