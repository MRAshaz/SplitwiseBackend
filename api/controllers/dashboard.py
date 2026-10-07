from ninja import Schema
from ninja_extra.controllers import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated

from api.models import Group, Expense, Settlement, Activity


class GroupBalanceOut(Schema):
    id: str
    name: str
    your_balance: float


class RecentActivityOut(Schema):
    id: str
    action: str
    actor: str
    metadata: dict
    created_at: str


class DashboardSummaryOut(Schema):
    total_owed_to_you: float
    total_you_owe: float
    net_balance: float
    groups: list[GroupBalanceOut]
    recent_activity: list[RecentActivityOut]


@api_controller("/dashboard/summary", tags=["Dashboard"], permissions=[IsAuthenticated])
class DashboardController:
    @http_get("/", response=DashboardSummaryOut)
    def summary(self, request):
        user = request.user
        groups = Group.objects.filter(members=user)

        group_balances = []
        total_owed_to_you = 0.0
        total_you_owe = 0.0

        for group in groups:
            balance = 0.0
            expenses = Expense.objects.filter(
                group=group, is_deleted=False
            ).prefetch_related("splits")
            for expense in expenses:
                for split in expense.splits.all():
                    if split.user_id == expense.paid_by_id:
                        continue
                    if expense.paid_by_id == user.id:
                        balance += float(split.amount_owed)
                    elif split.user_id == user.id:
                        balance -= float(split.amount_owed)

            settlements = Settlement.objects.filter(group=group)
            for s in settlements:
                if s.paid_by_id == user.id:
                    balance += float(s.amount)
                elif s.paid_to_id == user.id:
                    balance -= float(s.amount)

            group_balances.append(
                GroupBalanceOut(
                    id=str(group.id), name=group.name, your_balance=round(balance, 2)
                )
            )

            if balance > 0:
                total_owed_to_you += balance
            else:
                total_you_owe += abs(balance)

        recent_activity = (
            Activity.objects.filter(group__in=groups)
            .select_related("actor", "expense", "settlement")
            .order_by("-created_at")[:10]
        )

        activity_out = [
            RecentActivityOut(
                id=str(a.id),
                action=a.action,
                actor=a.actor.username if a.actor else "unknown",
                metadata=a.metadata,
                created_at=a.created_at.isoformat(),
            )
            for a in recent_activity
        ]

        return DashboardSummaryOut(
            total_owed_to_you=round(total_owed_to_you, 2),
            total_you_owe=round(total_you_owe, 2),
            net_balance=round(total_owed_to_you - total_you_owe, 2),
            groups=group_balances,
            recent_activity=activity_out,
        )
