from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Post, Group, Comment, Follow, User
from ..views import NUMBER


NUMBER_COUNT = 13


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='test-slug'
        )
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
        cls.post = Post.objects.create(
            text='Текст',
            group=cls.group,
            author=cls.user,
            image=uploaded
        )
        cls.comment = Comment.objects. create(
            text='Тут текст комментария',
            post=cls.post,
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:main'): 'posts/index.html',
            reverse('posts:group', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:add_comment', kwargs= {'post_id': self.post.id}):
            'posts/post_detail.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name, follow=True)
                self.assertTemplateUsed(response, template)
        cache.clear()
                

    def check_correct_context(self, response):
        response_post = response.context.get('page_obj')[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image_0 = response_post.image
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_image_0, self.post.image)

    def test_posts_main_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:main'))
        self.check_correct_context(response)
        cache.clear()

    def test_posts_group_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group', kwargs={'slug': 'test-slug'}))
        self.check_correct_context(response)
        cache.clear()

    def test_posts_profile_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.check_correct_context(response)
        cache.clear()

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        cache.clear()

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        cache.clear()

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'].text, self.post.text)
        post_count = response.context['post'].author.posts.count()
        self.assertEqual(self.post.author.posts.count(), post_count)
        cache.clear()

    def test_comment_exist_in_post_detail(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(len(response.context.get('comments')), 1)
        self.assertEqual(
            response.context.get('comments')[0].text,
            self.comment.text)
        cache.clear()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_title',
            description='test_description',
            slug='test-slug'
        )
        cls.group_2 = Group.objects.create(
            title='Заголовок-2',
            description='Описание-2',
            slug='test-slug-2'
        )
        for i in range(NUMBER_COUNT):
            cls.post = Post.objects.create(
                text='Текст',
                group=cls.group,
                author=cls.user
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        templates_page_names = {
            reverse('posts:main'): 'posts/index.html',
            reverse('posts:group', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), NUMBER
                )
        cache.clear()
                

    def test_second_page_contains_three_records(self):
        templates_page_names = {
            reverse('posts:main') + '?page=2': 'posts/index.html',
            reverse('posts:group', kwargs={'slug': self.group.slug})
            + '?page=2': 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username})
            + '?page=2': 'posts/profile.html',
        }
        for reverse_name, template in templates_page_names.items():
            response = self.client.get(reverse_name)
            self.assertEqual(len(
                response.context['page_obj']), NUMBER_COUNT - NUMBER)
        cache.clear()

    def test_new_post_is_not_in_wrong_group_2(self):
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': self.group_2.slug}))
        self.assertEqual(len(response.context.get('page_obj').object_list), 0)
        cache.clear()

class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_main(self):
        first_cond= self.authorized_client.get(reverse('posts:main'))
        post = Post.objects.get(id=1)
        post.text = 'Тут поменяли текст'
        post.save()
        second_cond = self.authorized_client.get(reverse('posts:main'))
        self.assertEqual(first_cond.content, second_cond.content)
        cache.clear()
        third_cond = self.authorized_client.get(reverse('posts:main'))
        self.assertNotEqual(first_cond.content, third_cond.content)


class FollowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.auth_follower = Client()
        self.auth_following = Client()
        self.follower = User.objects.create_user(username='follower')
        self.following = User.objects.create_user(username='following')
        self.auth_follower.force_login(self.follower)
        self.auth_following.force_login(self.following)

        self.post = Post.objects.create(
            author=self.following,
            text='Проверяем ленту новостей'
        )
        
    def test_follow_true(self):
        self.auth_follower.get(reverse('posts:profile_follow',
                               kwargs={'username': self.following.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_false(self):
        self.auth_follower.get(reverse('posts:profile_follow',
                               kwargs={'username': self.following.username}))
        self.auth_follower.get(reverse('posts:profile_unfollow',
                               kwargs={'username': self.following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)
