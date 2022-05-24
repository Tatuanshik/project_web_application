import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from ..models import Group, Post, User, Comment
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='just_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description=(
                'Текстовое описание должно быть длиннее, чтобы его проверить'
            )
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тексттт',
            group=cls.group
        )
        cls.comment = Comment.objects. create(
            text='Тут текст комментария',
            post=cls.post,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            )
        )
        new_post = Post.objects.latest('pub_date')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.author, self.post.author)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                group=self.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_create_post_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        login = reverse('users:login')
        create = reverse('posts:post_create')
        self.assertRedirects(
            response,
            f'{login}?next={create}',
        )
        self.assertEqual(Post.objects.count(), posts_count + 0)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Что-то новенькое добавлено',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('pub_date')

        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.id}))
        self.assertEqual(form_data['text'], new_post.text)
        self.assertEqual(Post.objects.count(), posts_count + 0)

    def test_comment_form_authorized_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text,
            'group': self.group.id,
        }
        new_comment = Comment.objects.latest('text')
        self.assertEqual(form_data['text'], new_comment.text)
        self.assertEqual(Comment.objects.count(), comment_count + 0)
