from rest_framework.routers import SimpleRouter

from .views import GroupViewSet, UserViewSet


router = SimpleRouter()
router.register('users', UserViewSet)
router.register('groups', GroupViewSet)

urlpatterns = router.urls
