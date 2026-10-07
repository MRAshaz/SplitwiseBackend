from ninja_extra.controllers import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from ninja.errors import HttpError
from api.schemas import RegisterIn, RegisterOut, UserOut, LoginIn, TokenOut

User = get_user_model()


@api_controller("/auth", tags=["auth"])
class AuthController:
    @http_post("/register", response=RegisterOut, auth=None)
    def register(self, payload: RegisterIn):
        if User.objects.filter(username=payload.username).exists():
            raise HttpError(400, "Username already taken!")
        if User.objects.filter(email=payload.email).exists():
            raise HttpError(400, "Email already registered!")

        user = User.objects.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )
        return user

    @http_post("/login", response=TokenOut, auth=None)
    def login(self, payload: LoginIn):
        user = authenticate(username=payload.username, password=payload.password)
        if not user:
            raise HttpError(401, "Invalid credentials!")
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @http_get("/me", response=UserOut, permissions=[IsAuthenticated])
    def me(self, request):
        return request.user
