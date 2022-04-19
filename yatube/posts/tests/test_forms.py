import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.form_comment_data = {
            'text': 'Каммент'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_data = {
            'text': 'Тестовый текст 2',
            'group': 1,
        }

    def test_post_create_and_edit_form(self):
        """Валидная форма создает и редактирует запись в Posts."""
        form_urls = {
            reverse(
                'posts:post_edit', args={1}
            ): [reverse('posts:post_detail', args={1}), 1],
            reverse('posts:post_create'): [reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ), 2],
        }
        for form_url, (redic_url, count) in form_urls.items():
            with self.subTest(form_url):
                uploaded = SimpleUploadedFile(
                    name='gif_image.gif',
                    content=self.small_gif,
                    content_type='image/gif'
                )
                self.form_data.update({'image': uploaded})
                response = self.authorized_client.post(
                    form_url,
                    data=self.form_data,
                )
                self.assertRedirects(response, redic_url)
                self.assertEqual(Post.objects.count(), count)
                self.assertTrue(
                    Post.objects.filter(
                        group=self.group,
                        text=self.form_data['text'],
                        image='posts/gif_image.gif'
                    ).exists()
                )

    def test_guest_user_cant_create_and_edit_posts(self):
        """Неавторизованный пользователь не может создавать/редактировать
        посты"""
        form_urls = [
            reverse('posts:post_edit', args={1}),
            reverse('posts:post_create'),
        ]
        count_posts = 1
        for form_url in form_urls:
            with self.subTest(form_url):
                response = self.guest_client.post(
                    form_url,
                    data=self.form_data,
                )
                self.assertEqual(response.status_code, 302)
                self.assertIn('/auth/login/', response.url)
                self.assertEqual(Post.objects.count(), count_posts)
                self.assertFalse(
                    Post.objects.filter(
                        group=self.group,
                        text=self.form_data['text'],
                    ).exists()
                )

    def test_auth_user_cant_edit_not_own_post(self):
        """Авторизованный пользователь не может редактировать чужой пост."""
        user2 = User.objects.create_user(username='test_user2')
        authorized_client = Client()
        authorized_client.force_login(user2)

        response = authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk
            }),
            data=self.form_data,
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        self.assertFalse(
            Post.objects.filter(
                group=self.group,
                text=self.form_data['text'],
            ).exists()
        )

    def test_guest_user_cant_comment_post(self):
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.pk
            }),
            data=self.form_comment_data,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_auth_user_can_comment_post(self):
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.pk
            }),
            data=self.form_comment_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.pk
        }))
        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(
            Comment.objects.filter(
                text=self.form_comment_data['text'],
            ).exists()
        )
        self.assertEqual(
            response.context['post'].comments.all()[0].text,
            self.form_comment_data['text']
        )
