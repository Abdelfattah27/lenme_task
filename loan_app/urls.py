from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import  LoanRequestViewSet, LoanOfferViewSet , UserRegistrationView

router = DefaultRouter()
router.register(r'loan-requests', LoanRequestViewSet)
router.register(r'loan-offers', LoanOfferViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),

]
