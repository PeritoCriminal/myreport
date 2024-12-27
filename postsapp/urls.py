# postsapp/urls.py


from django.urls import path
from postsapp.views import (create_or_edit_post,
                            show_posts_view, delete_post,
                            hide_post,
                            liked_post,
                            save_comment,
                            toggle_comment_like,
                            delete_comment_view,
                            liked_comment,
                            )

urlpatterns = [
    path('create_post/', create_or_edit_post, name='create_post'),
    path('edit_post/<int:post_id>/', create_or_edit_post, name='edit_post'),
    path('show_post', show_posts_view, name='show_posts'),
    path('post/delete/<int:post_id>/', delete_post, name='delete_post'),
    path('hide_post/<int:post_id>/', hide_post, name='hide_post'),
    path('posts/like/<int:post_id>/', liked_post, name='liked_post'),
    path('save_comment/', save_comment, name='save_comment'), 
    path('liked_comment/<int:comment_id>/', liked_comment, name='liked_comment'),
    path('delete_comment/<int:comment_id>/', delete_comment_view, name='delete_comment'),


]