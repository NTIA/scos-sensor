from rest_framework.routers import SimpleRouter

from .views import ScheduleEntryViewSet


router = SimpleRouter()
router.register('', ScheduleEntryViewSet, base_name='schedule')


urlpatterns = router.urls
