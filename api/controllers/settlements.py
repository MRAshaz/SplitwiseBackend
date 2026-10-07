import uuid
from decimal import Decimal, ROUND_HALF_UP
from ninja_extra.controllers import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated
from ninja.errors import HttpError
from api.models import Settlement, Group
from api.schemas import SettlementIn, SettlementOut
from api.utils.activity import log_activity


@api_controller("/groups/{group_id}/settlements", tags=["Settlements"], permissions=[])
class SettlementController:
    def _get_object_or_404(self, request, group_id: uuid.UUID):
        try:
            return Group.objects.get(id=group_id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")

    @http_get("/", response=list[SettlementOut])
    def list_settlements(self, request, group_id: uuid.UUID):
        group = self._get_object_or_404(request, group_id)
        return (
            Settlement.objects.filter(group=group)
            .select_related("paid_by", "paid_to")
            .order_by("-created_at")
        )

    @http_post("/", response=SettlementOut)
    def create_settlement(self, request, group_id: uuid.UUID, payload: SettlementIn):
        group = self._get_object_or_404(request, group_id)

        amount = Decimal(str(payload.amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if amount <= 0:
            raise HttpError(400, "Amount must be positive!")

        if not group.members.filter(id=payload.paid_to_id).exists():
            raise HttpError(400, "paid_to must be a member of this group!")

        if payload.paid_to_id == request.user.id:
            raise HttpError(400, "Cannot settle with yourself!")

        settlement = Settlement.objects.create(
            group=group,
            paid_by=request.user,
            paid_to_id=payload.paid_to_id,
            amount=amount,
            note=payload.note,
        )

        log_activity(
            group=group,
            actor=request.user,
            action="settlement_created",
            metadata={
                "amount": str(settlement.amount),
                "paid_to": settlement.paid_to.username,
            },
        )

        return Settlement.objects.select_related("paid_by", "paid_to").get(
            id=settlement.id
        )
