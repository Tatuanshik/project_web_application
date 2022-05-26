from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

NUMBER: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    posts = group.posts.all()
    paginator = Paginator(posts, NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_count = posts.count()
    paginator = Paginator(posts, NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/profile.html'
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form_comment = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form_comment': form_comment,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        context = {'form': form}
        return render(request, template, context)
    post_create = form.save(commit=False)
    post_create.author = request.user
    post_create.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None, instance=post,
                    files=request.FILES or None)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if not form.is_valid():
        context = {'form': form, 'is_edit': True, 'post': post}
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    info_posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(info_posts, NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user 
    if author != user:
        Follow.objects.get_or_create(
            author=author,
            user=user,
        )
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
