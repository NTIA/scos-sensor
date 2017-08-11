from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns

from .views import UserViewSet


router = SimpleRouter()
router.register('users', UserViewSet)

urlpatterns = (

)
router.urls
