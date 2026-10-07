import uuid
from ninja_extra.controllers import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated
from ninja.errors import HttpError
from api.models import Group, Activity
from api.schemas import ActivityOut


@api_controller("/groups/{group_id}/activiy", tags=["Activity"], permissions=[])
class ActivityController:
    def _get_group_or_404(self, request, group_id: uuid.UUID):
        try:
            Group.objects.get(id=group_id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")

    @http_get("/", response=list[ActivityOut])
    def list_activity(self, request, group_id: uuid.UUID):
        group = self._get_group_or_404(request, group_id)
        return (
            Activity.objects.filter(group=group)
            .select_related("actor", "expense", "settlement")
            .order_by("-created_at")
        )
