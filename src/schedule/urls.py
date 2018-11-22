from rest_framework.routers import SimpleRouter

from .views import ScheduleEntryViewSet

router = SimpleRouter()
router.register('', ScheduleEntryViewSet, basename='schedule')

urlpatterns = router.urls
