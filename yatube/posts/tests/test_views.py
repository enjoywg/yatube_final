import shutil
import tempfile
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post
from ..views import POSTS_ON_PAGE

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostSetUpTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.pages_with_posts = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username})
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PostsViewsTests(PostSetUpTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            text='Каммент',
            author=cls.user,
            post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_views_use_correct_template(self):
        """View использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_posts_show_correct_context(self):
        """Шаблоны с выводом постов сформированы с правильным контекстом."""
        for page in self.pages_with_posts:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                first_post = response.context['page_obj'][0]
                self.assertEqual(first_post.text, 'Тестовый пост')
                self.assertEqual(type(first_post.pub_date), datetime)
                self.assertEqual(first_post.author, self.user)
                self.assertEqual(first_post.group, self.group)

    def test_post_index_show_correct_context(self):
        """Шаблон post_index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        title = response.context['title']
        self.assertEqual(title, 'Последние обновления на сайте')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        self.assertEqual(group, self.group)

    def test_posts_profile_show_correct_context(self):
        """Шаблон posts_profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        user = response.context['user_obj']
        self.assertEqual(user, self.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context['post']
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(type(post.pub_date), datetime)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.comments.all()[0].text, self.comment.text)

    def test_post_edit_and_post_create_show_correct_context(self):
        """Шаблон post_create и post_edit сформированы с правильной формой
        из контекста."""
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        post_id = response.context['post_id']
        is_edit = response.context['is_edit']
        self.assertEqual(post_id, self.post.pk)
        self.assertTrue(is_edit)

    def test_post_with_group_exists_in_pages(self):
        """Пост с указанной группой появляется на страницах: главной, группы и
        юзера"""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in urls:
            with self.subTest(reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0], self.post
                )

    def test_post_not_exists_in_other_group(self):
        """Пост не попал в группу, для которой не был предназначен"""
        group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        reverse_name = reverse(
            'posts:group_list', kwargs={'slug': group2.slug}
        )
        response = self.authorized_client.get(reverse_name)
        self.assertFalse(self.post in response.context['page_obj'])

    def test_posts_index_cache(self):
        post_2 = Post.objects.create(
            author=self.user,
            text='Тестовыйddddddd пост 2',
            group=self.group,
        )
        cache.clear()
        self.authorized_client.get(reverse('posts:index')).content
        post_2.delete()
        content_after_delete = self.authorized_client.get(
            reverse('posts:index')).content

        self.assertIn(post_2.text.encode(), content_after_delete)
        self.assertEqual(Post.objects.all().count(), 1)

        cache.clear()
        content_after_clear_cache = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotIn(post_2.text.encode(), content_after_clear_cache)


class PaginatorViewsTest(PostSetUpTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.bulk_create(
            Post(
                author=cls.user,
                text=f'Тестовый пост {i + 1}',
                group=cls.group
            )
            for i in range(POSTS_ON_PAGE + 7)
        )

    def setUp(self):
        self.guest_client = Client()

    def test_paginator(self):
        """Паджинатор отображает верное количество постов"""
        urls = {
            reverse('posts:index'): POSTS_ON_PAGE,
            reverse('posts:index') + '?page=2': 7,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): POSTS_ON_PAGE,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2': 7,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): POSTS_ON_PAGE,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ) + '?page=2': 7
        }
        for url, count_posts in urls.items():
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), count_posts
                )


class PostsViewsImageTestCase(PostSetUpTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='hgngh.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с картинкой',
            group=cls.group,
            image=uploaded
        )
        cls.guest_client = Client()

    def test_pages_with_posts_has_image_in_context(self):
        for page in self.pages_with_posts:
            with self.subTest(page=page):
                response = self.guest_client.get(page)

        image_name = response.context['page_obj'][0].image.name
        self.assertIn(self.post.image.name, image_name)

    def test_post_detail_has_image_in_context(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        image_name = response.context['post'].image.name
        self.assertIn(self.post.image.name, image_name)


class PostsFollowTestCase(PostSetUpTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post_author = Post.objects.create(
            author=cls.author,
            text='Пост автора',
            group=cls.group,
        )
        cls.new_author_post = Post.objects.create(
            author=cls.author,
            text='Новый пост автора',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_auth_user_can_follow_other_user(self):
        url = reverse('posts:profile_follow', kwargs={'username': self.author})
        self.authorized_client.get(url)

        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author
        ).exists())

    def test_auth_user_can_unfollow_other_users(self):
        Follow.objects.create(user=self.user, author=self.author)
        url = reverse(
            'posts:profile_unfollow', kwargs={'username': self.author}
        )
        self.authorized_client.get(url)

        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.author
        ).exists())

    def test_new_author_post_exists_in_follower_feed(self):
        Follow.objects.create(user=self.user, author=self.author)
        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)

        self.assertEqual(
            response.context['page_obj'][0].text, self.new_author_post.text
        )

    def test_new_author_post_notexists_in_nofollower_feed(self):
        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)

        self.assertFalse(
            response.context['page_obj']
        )
