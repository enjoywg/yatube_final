from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import SLICE_SIZE, Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 10,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий ' * 10,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        object_names = {
            str(self.post): self.post.text[:SLICE_SIZE],
            str(self.group): self.group.title,
            str(self.comment): self.comment.text[:SLICE_SIZE],
        }
        for object_name, expected_value in object_names.items():
            with self.subTest(object_name):
                self.assertEqual(object_name, expected_value)

    def test_verbose_names(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_follow(self):
        Follow.objects.create(
            user=self.user,
            author=self.author
        )

        self.assertTrue(
            Follow.objects.get(user=self.user, author=self.author)
        )
