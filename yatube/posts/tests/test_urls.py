from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Follow, Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.public_urls = [
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html'),
        ]
        cls.private_urls = [
            (f'/posts/{cls.post.pk}/edit/',
             'posts/create_post.html'),
            ('/create/', 'posts/create_post.html'),
            ('/follow/', 'posts/follow.html'),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_http_answer_for_guests(self):
        """URL-адрес дает корректный ответ для гостевых клиентов"""
        for url, _ in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        """Несуществующий URL-адрес дает ответ 404"""
        noexists_page = '/dsfdfv/'
        response = self.guest_client.get(noexists_page)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_http_answer_for_authorized_users(self):
        """URL-адрес дает корректный ответ для авторизованных клиентов"""
        for url, _ in self.private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_posts_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in (self.public_urls
                              + self.private_urls):
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_follow_url(self):
        author = User.objects.create_user(username='author')
        response = self.authorized_client.get(
            f'/profile/{author.username}/follow/'
        )
        self.assertRedirects(response, f'/profile/{author.username}/')

    def test_unfollow_url(self):
        author = User.objects.create_user(username='author')
        Follow.objects.create(
            user=self.user,
            author=author
        )
        response = self.authorized_client.get(
            f'/profile/{author.username}/unfollow/'
        )
        self.assertRedirects(response, f'/profile/{author.username}/')
