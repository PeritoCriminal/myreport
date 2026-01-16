from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User
from groups.models import Group, GroupMembership


class GroupsModelsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="TestPass!12345",
        )
        cls.group = Group.objects.create(
            name="Grupo X",
            description="Desc",
            creator=cls.user,
        )

    def test_group_str_returns_name(self):
        self.assertEqual(str(self.group), "Grupo X")

    def test_group_name_is_unique(self):
        with self.assertRaises(IntegrityError):
            Group.objects.create(
                name="Grupo X",
                description="Outro",
                creator=self.user,
            )

    def test_membership_unique_constraint(self):
        GroupMembership.objects.create(group=self.group, user=self.user)

        with self.assertRaises(IntegrityError):
            GroupMembership.objects.create(group=self.group, user=self.user)

    def test_membership_str_contains_user_and_group(self):
        m = GroupMembership.objects.create(group=self.group, user=self.user)
        self.assertIn("Grupo X", str(m))
        self.assertIn(self.user.username, str(m))
