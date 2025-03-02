from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, LogoutView, RegisterView,
    CourierViewSet, ProductViewSet, RegionViewSet,
    CityViewSet, AssignProductView, FileUploadView,
    CourierCreateAPIView, MyTokenObtainPairView, CourierProductListView,
    ConfirmReceiptProductView, ConfirmDeliveredProductView
)

router = DefaultRouter()
router.register(r'couriers', CourierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'cities', CityViewSet)
router.register(r'regions', RegionViewSet)

urlpatterns = [
    path('couriers/create/', CourierCreateAPIView.as_view(), name='courier-create'),
    path('courier/products/', CourierProductListView.as_view(), name='courier-products'),
    path('confirm-receipt/', ConfirmReceiptProductView.as_view(), name='confirm-receipt'),
    path('confirm-delivered/', ConfirmDeliveredProductView.as_view(), name='confirm-delivered'),
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('assign-product/', AssignProductView.as_view(), name='assign-product'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]
