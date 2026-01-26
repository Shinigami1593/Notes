from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NoteViewSet
from . import payments

router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
    # eSewa payment routes
    path('payments/esewa/initiate/', payments.initiate_esewa_payment, name='initiate_esewa'),
    path('payments/esewa/success/', payments.esewa_success, name='esewa_success'),
    path('payments/esewa/failure/', payments.esewa_failure, name='esewa_failure'),
    path('payments/verify/<str:transaction_uuid>/', payments.verify_payment, name='verify_payment'),
]
