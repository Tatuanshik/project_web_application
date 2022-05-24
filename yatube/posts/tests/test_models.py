from django.test import TestCase
from ..models import Group, Post, User


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовыыый пост'
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTests.post
        exp_object_name_text = post.text[:15]
        self.assertEqual(exp_object_name_text, str(post))

        group = PostModelTests.group
        exp_object_name_title = group.title
        self.assertEqual(exp_object_name_title, str(group))
