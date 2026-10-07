from ninja_extra.controllers import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from api.schemas import UserPublicOut

User = get_user_model()


@api_controller("/users", tags=["Users"], permissions=[IsAuthenticated])
class UserController:
    @http_get("/lookup/", response=UserPublicOut)
    def lookup_users(self, request, username: str):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise HttpError(404, "User not found!")
        if user.id == request.user.id:
            raise HttpError(400, "That's you!")
        return user

    @http_get("/{user_id}/", response=UserPublicOut)
    def get_user(self, request, user_id: int):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise HttpError(404, "User not found!")
