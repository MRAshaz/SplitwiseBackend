import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from ninja_extra.controllers import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated
from ninja.errors import HttpError
from api.schemas import ExpenseIn, ExpenseOut
from api.models import Expense, Group, ExpenseSplit
from api.utils.activity import log_activity


@api_controller(
    "/groups/{group_id}/expenses", tags=["Expenses"], permissions=[IsAuthenticated]
)
class ExpenseController:
    def _get_group_or_404(self, request, id: uuid.UUID) -> Group:
        try:
            return Group.objects.get(id=id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")

    @http_get("/", response=list[ExpenseOut])
    def list_expenses(self, request, group_id: uuid.UUID):
        group = self._get_group_or_404(request, group_id)
        return (
            Expense.objects.filter(group=group, is_deleted=False)
            .select_related("paid_by", "category")
            .prefetch_related("splits__user")
            .order_by("-date", "-created_at")
        )

    @http_post("/", response=ExpenseOut)
    def create_expense(self, request, group_id: uuid.UUID, payload: ExpenseIn):
        group = self._get_group_or_404(request, group_id)

        if not payload.splits:
            raise HttpError(400, "At least one split is required!")

        splits_total = sum(Decimal(str(s.amount_owed)) for s in payload.splits)
        expense_amount = Decimal(str(payload.amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if (
            splits_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            != expense_amount
        ):
            raise HttpError(
                400,
                f"Splits sum to {splits_total}, but expense amount is {expense_amount}",
            )

        member_ids = set(group.members.values_list("id", flat=True))
        for split in payload.splits:
            if split.user_id not in member_ids:
                raise HttpError(400, f"User {split.user_id} is not a member of this")

        with transaction.atomic():
            expense = Expense.objects.create(
                group=group,
                description=payload.description,
                amount=expense_amount,
                currency=payload.currency,
                category_id=payload.category_id,
                paid_by=request.user,
                created_by=request.user,
                split_type=payload.split_type,
                date=payload.date,
            )

            ExpenseSplit.objects.bulk_create(
                [
                    ExpenseSplit(
                        expense=expense,
                        user_id=split.user_id,
                        amount_owed=split.amount_owed,
                        is_settled=(split.user_id == request.user.id),
                    )
                    for split in payload.splits
                ]
            )

        log_activity(
            group=group,
            actor=request.user,
            action="expense_created",
            expense=expense,
            metadata={
                "description": expense.description,
                "amount": str(expense.amount),
            },
        )

        return (
            Expense.objects.select_related("paid_by", "category")
            .prefetch_related("splits__user")
            .get(id=expense.id)
        )
