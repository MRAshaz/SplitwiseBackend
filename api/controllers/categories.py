from ninja_extra.controllers import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated
from ninja.errors import HttpError
from api.models import Category
from api.schemas import CategoryIn, CategoryOut


@api_controller("/categories", tags=["Categories"], permissions=[])
class CategoryController:
    @http_get("/", response=list[CategoryOut])
    def list_categories(self, request):
        return Category.objects.all().order_by("name")

    @http_post("/", response=CategoryOut)
    def create_category(self, request, payload: CategoryIn):
        if Category.objects.filter(name__iexact=payload.name).exists():
            raise HttpError(400, "Category already exists!")

        category = Category.objects.create(name=payload.name, icon=payload.icon or "")
        return category
