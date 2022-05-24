from django import forms
from .models import Post, Comment, Follow


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {
            'text': 'Текст поста',
            'group': 'Группы',
        }
        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
            'image': 'Загружаем фото в пост',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
    

class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        labels = {
            'user': 'Подписка', 
            'author': 'Автор поста',
        }
        fields = ('user',)