from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from api.controllers.auth import AuthController
from api.controllers.groups import GroupController
from api.controllers.expenses import ExpenseController
from api.controllers.activity import ActivityController
from api.controllers.settlements import SettlementController
from api.controllers.categories import CategoryController
from api.controllers.dashboard import DashboardController
from api.controllers.friends import FriendController, FiendSettlementController
from api.controllers.users import UserController
from api.models import User
from api.schemas import UserPublicOut

api = NinjaExtraAPI(auth=JWTAuth())
api.register_controllers(
    AuthController,
    GroupController,
    ExpenseController,
    SettlementController,
    ActivityController,
    CategoryController,
    DashboardController,
    FriendController,
    FiendSettlementController,
    UserController,
)


@api.get("/", auth=None, response=list[UserPublicOut])
def get_user(request):
    return User.objects.all()
