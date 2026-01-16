from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from social_net.models import Post, PostLike, PostRating, PostComment, PostHidden
from social_net.forms import PostCommentForm


class SocialNetModelsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPass!12345"

        cls.u1 = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password=cls.password,
        )
        cls.u2 = User.objects.create_user(
            username="u2",
            email="u2@example.com",
            password=cls.password,
        )

        cls.post = Post.objects.create(
            user=cls.u1,
            title="Post",
            text="Texto",
            is_active=True,
        )

    # -------------------------
    # PostLike
    # -------------------------

    def test_postlike_unique_constraint(self):
        PostLike.objects.create(post=self.post, user=self.u2)

        with self.assertRaises(IntegrityError):
            PostLike.objects.create(post=self.post, user=self.u2)

    # -------------------------
    # PostRating
    # -------------------------

    def test_postrating_unique_constraint(self):
        PostRating.objects.create(post=self.post, user=self.u2, value=5)

        with self.assertRaises(IntegrityError):
            PostRating.objects.create(post=self.post, user=self.u2, value=4)

    def test_postrating_value_check_constraint(self):
        # value = 0
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PostRating.objects.create(post=self.post, user=self.u2, value=0)

        # value = 6
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PostRating.objects.create(post=self.post, user=self.u2, value=6)



    # -------------------------
    # PostHidden
    # -------------------------

    def test_posthidden_unique_constraint(self):
        PostHidden.objects.create(post=self.post, user=self.u2)

        with self.assertRaises(IntegrityError):
            PostHidden.objects.create(post=self.post, user=self.u2)

    # -------------------------
    # PostComment
    # -------------------------

    def test_comment_requires_text_or_image_validation(self):
        form = PostCommentForm(data={"text": ""}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn("Informe texto ou imagem.", form.non_field_errors())

    def test_comment_form_strips_text(self):
        form = PostCommentForm(data={"text": "  oi  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["text"], "oi")



    # -------------------------
    # __str__ (barato e útil)
    # -------------------------

    def test_post_str(self):
        s = str(self.post)
        self.assertIn("Post", s)
        self.assertIn(str(self.u1.id), s)

    def test_posthidden_str(self):
        h = PostHidden.objects.create(post=self.post, user=self.u2)
        s = str(h)
        self.assertIn("ocultou", s)
