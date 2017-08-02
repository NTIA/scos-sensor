from rest_framework.routers import SimpleRouter

from .views import StatusViewSet


router = SimpleRouter()
router.register('', StatusViewSet, base_name='status')

urlpatterns = router.urls
