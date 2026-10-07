import uuid
from ninja import Schema
from ninja_extra.controllers import (
    api_controller,
    http_get,
    http_post,
    http_patch,
    http_delete,
)
from ninja.errors import HttpError
from ninja_extra.permissions import IsAuthenticated
from api.schemas import GroupIn, GroupOut, DeleteOut
from django.contrib.auth import get_user_model
from api.models import Group
from api.utils.activity import log_activity

User = get_user_model()


class AddMemberIn(Schema):
    username: str


@api_controller("/groups", tags=["Groups"], permissions=[IsAuthenticated])
class GroupController:
    def _get_object_or_404(self, request, group_id: uuid.UUID):
        try:
            return Group.objects.get(id=group_id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")

    @http_get("/", response=list[GroupOut])
    def list_groups(self, request):
        groups = Group.objects.filter(members=request.user)
        return groups

    @http_get("/{id}/", response=GroupOut)
    def get_group(self, request, id: uuid.UUID):
        try:
            group = Group.objects.get(id=id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")
        return group

    @http_post("/", response=GroupOut)
    def create_group(self, request, payload: GroupIn):
        group = Group.objects.create(
            name=payload.name,
            created_by=request.user,
        )
        group.members.add(request.user)
        log_activity(
            group=group,
            actor=request.user,
            action="member_added",
            metadata={"username": request.user.username},
        )
        return group

    @http_post("/{id}/members/", response=GroupOut)
    def add_members(self, request, id: uuid.UUID, payload: AddMemberIn):
        try:
            group = Group.objects.get(id=id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")

        try:
            new_member = User.objects.get(username=payload.username)
        except User.DoesNotExist:
            raise HttpError(404, "User not found!")

        if group.members.filter(id=new_member.id).exists():
            raise HttpError(400, "User is already a member of this group!")

        group.members.add(new_member)

        log_activity(
            group=group,
            actor=request.user,
            action="member_added",
            metadata={"username": new_member.username},
        )
        return Group.objects.prefetch_related("members").get(id=group.id)

    @http_delete("/{id}/members/{user_id}/", response={"success": bool})
    def remove_member(self, request, id: uuid.UUID, user_id: int):
        try:
            group = Group.objects.get(id=id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found!")

        try:
            member_to_remove = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise HttpError(404, "User not found!")

        if not group.members.filter(id=user_id).exists():
            raise HttpError(400, "User is not a member of this group!")

        if not group.members.id == group.created_by.id:
            raise HttpError(400, "Cannot remove the group creator!")

        group.members.remove(member_to_remove)

        log_activity(
            group=group,
            actor=request.user,
            action="member_removed",
            metadata={"username": member_to_remove.username},
        )

        return {"success": True}

    @http_delete("/{id}/", response=DeleteOut)
    def delete_group(self, id: uuid.UUID):
        try:
            group = Group.objects.get(id=id).delete()
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found")
        return {"success": True}

    @http_patch("/{id}/", response=GroupOut)
    def update_group(self, request, id: uuid.UUID, payload: GroupIn):
        try:
            group = Group.objects.get(id=id, members=request.user)
        except Group.DoesNotExist:
            raise HttpError(404, "Group not found")
        for attr, val in payload.dict().items():
            setattr(group, attr, val)
        group.save()
        return group
