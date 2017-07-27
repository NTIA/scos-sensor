from rest_framework.viewsets import ViewSet

from .models import Acquisition
from .serializers import AcquisitionSerializer


class AcquisitionViewSet(ViewSet):
    def list(self, request):
        pass

    def retrieve(self, request, entry):
        pass

    def destroy(self, request, entry):
        pass
