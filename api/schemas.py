import uuid
from datetime import date
from decimal import Decimal
from api.models import (
    Group,
    GroupMembership,
    Category,
    Expense,
    ExpenseSplit,
    Settlement,
    Activity,
)
from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema

User = get_user_model()


class RegisterIn(Schema):
    username: str
    email: str
    password: str


class RegisterOut(Schema):
    id: int
    username: str
    email: str


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class UserOut(ModelSchema):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class UserIn(Schema):
    username: str
    email: str
    password: str


class UserPublicOut(Schema):
    id: int
    username: str


class GroupOut(ModelSchema):
    created_by: UserPublicOut | None = None
    members: list[UserPublicOut] = []

    class Meta:
        model = Group
        fields = ["id", "name", "image"]
        fields_optional = ["image"]

    @staticmethod
    def resolve_members(obj):
        return list(obj.members.all())


class GroupIn(Schema):
    name: str


class UserMembershipOut(ModelSchema):
    user: UserPublicOut

    class Meta:
        model = GroupMembership
        fields = ["role", "joined_at"]


class GroupMembershipOut(ModelSchema):
    group: GroupOut

    class Meta:
        model = GroupMembership
        fields = ["role", "joined_at"]


class CategoryOut(ModelSchema):
    class Meta:
        model = Category
        fields = ["name", "icon"]
        fields_optional = ["icon"]


class CategoryIn(ModelSchema):
    class Meta:
        model = Category
        fields = ["name", "icon"]


class ExpenseSplitOut(ModelSchema):
    user: UserPublicOut
    amount_owed: float

    class Meta:
        model = ExpenseSplit
        fields = ["percentage", "shares", "is_settled"]
        fields_optional = ["percentage", "shares"]


class ExpenseSplitIn(Schema):
    user_id: int
    amount_owed: Decimal
    percentage: Decimal | None = None
    shares: int | None = None


class ExpenseOut(ModelSchema):
    group: GroupOut | None = None
    paid_by: UserPublicOut
    created_by: UserPublicOut
    category: CategoryOut | None = None
    splits: list[ExpenseSplitOut]
    amount: float

    class Meta:
        model = Expense
        fields = [
            "id",
            "description",
            # "amount",
            "currency",
            "split_type",
            "date",
            "created_at",
            "updated_at",
            "is_deleted",
        ]


class ExpenseIn(Schema):
    description: str
    amount: Decimal
    currency: str = "USD"
    split_type: str
    date: date
    group_id: uuid.UUID | None = None
    category_id: int | None = None
    splits: list[ExpenseSplitIn]


class SettlementOut(ModelSchema):
    group: GroupOut | None = None
    paid_by: UserPublicOut
    paid_to: UserPublicOut
    amount: float

    class Meta:
        model = Settlement
        fields = ["id", "currency", "note", "created_at"]


class SettlementIn(Schema):
    paid_to_id: int
    amount: Decimal
    currency: str = "USD"
    note: str = ""
    group_id: uuid.UUID | None = None


class ActivityOut(ModelSchema):
    group: GroupOut | None = None
    actor: UserPublicOut | None = None
    expense: ExpenseOut | None = None
    settlement: SettlementOut | None = None

    class Meta:
        model = Activity
        fields = ["action", "metadata", "created_at"]


class DeleteOut(Schema):
    success: bool
