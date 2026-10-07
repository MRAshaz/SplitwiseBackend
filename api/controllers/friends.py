from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction, models
from ninja_extra.controllers import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated
from ninja.errors import HttpError
from api.models import Expense, ExpenseSplit, Settlement
from api.schemas import ExpenseIn, ExpenseOut, SettlementOut, SettlementIn


@api_controller("/friends/expenses", tags=["Friends"], permissions=[IsAuthenticated])
class FriendController:
    @http_get("/", response=list[ExpenseOut])
    def list_friend_expenses(self, request):
        return (
            Expense.objects.filter(group__isnull=True, is_deleted=False)
            .filter(splits__user=request.user)
            .select_related("paid_by", "category")
            .prefetch_related("splits__user")
            .distinct()
            .order_by("-date", "-created_at")
        )

    @http_post("/", response=ExpenseOut)
    def create_frined_expenses(self, request, payload: ExpenseIn):
        if not payload.splits:
            raise HttpError(400, "At least one split is required!")
        if len(payload.splits) != 2:
            raise HttpError(400, "Friend expenses must have exactly 2 people")

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

        if request.user.id not in [s.user_id for s in payload.splits]:
            raise HttpError(
                400, "You must be one of the two people in a friend expense"
            )

        with transaction.atomic():
            expense = Expense.objects.create(
                group=None,
                description=payload.description,
                amount=payload.amount,
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

            return (
                Expense.objects.select_related("paid_by", "category")
                .prefetch_related("splits__user")
                .get(id=expense.id)
            )


@api_controller("/friends/settlements", tags=["Friends"], permissions=[IsAuthenticated])
class FiendSettlementController:
    @http_get("/", response=list[SettlementOut])
    def list_friend_settlements(self, request):
        return (
            Settlement.objects.filter(group__isnull=True)
            .filter(models.Q(paid_by=request.user) | models.Q(paid_to=request.user))
            .select_related("paid_by", "paid_to")
            .order_by("-created_at")
        )

    @http_post("/", response=SettlementOut)
    def create_friend_settlement(self, request, payload: SettlementIn):
        amount = Decimal(str(payload.amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if amount < 0:
            raise HttpError(400, "Amount must be positive!")
        if payload.paid_to_id == request.user.id:
            raise HttpError(400, "Cannot settle with yourself!")

        settlement = Settlement.objects.create(
            group=None,
            paid_by=request.user,
            paid_to_id=payload.paid_to_id,
            amount=payload.amount,
            currency=payload.currency,
            note=payload.note,
        )
        return Settlement.objects.select_related("paid_by", "paid_to").get(
            id=settlement.id
        )
