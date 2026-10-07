from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser
from django.conf import settings
from django.db import models
from decimal import Decimal
import uuid


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_groups",
    )
    image = models.ImageField(upload_to="group_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        User, through="GroupMembership", related_name="splitwise_groups"
    )


class GroupMembership(models.Model):
    ROLE_CHOICES = [("admin", "Admin"), ("member", "Member")]
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "categories"


class Expense(models.Model):
    SPLIT_TYPE_CHOICE = [
        ("equal", "Equal"),
        ("exact", "Exact Amount"),
        ("percentage", "Percentage"),
        ("shares", "Shares"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, null=True, blank=True, related_name="expenses"
    )
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, default="INR")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    paid_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="paid_expenses"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_expenses"
    )
    split_type = models.CharField(
        max_length=10, choices=SPLIT_TYPE_CHOICE, default="equal"
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["group", "date"]),
            models.Index(fields=["paid_by"]),
        ]


class ExpenseSplit(models.Model):
    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE, related_name="splits"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=12, decimal_places=2)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    shares = models.PositiveIntegerField(null=True, blank=True)
    is_settled = models.BooleanField(default=False)

    class Meta:
        unique_together = ("expense", "user")


class Settlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    paid_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="settlements_paid"
    )
    paid_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="settlements_received"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Activity(models.Model):
    ACTION_CHOICES = [
        ("expense_created", "Expense Created"),
        ("expense_updated", "Expense Updated"),
        ("expense_deleted", "Expense Deleted"),
        ("settlement_created", "Expense Created"),
        ("member_added", "Member Added"),
        ("member_removed", "Member Removed"),
    ]
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="activities",
    )
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    expense = models.ForeignKey(
        Expense, on_delete=models.SET_NULL, null=True, blank=True
    )
    settlement = models.ForeignKey(
        Settlement, on_delete=models.SET_NULL, null=True, blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "activities"
