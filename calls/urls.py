from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallViewSet, ManagerViewSet

router = DefaultRouter()
router.register(r"calls", CallViewSet, basename="call")
router.register(r"managers", ManagerViewSet, basename="manager")

urlpatterns = [
    path("", include(router.urls)),
]
