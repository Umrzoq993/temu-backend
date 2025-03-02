from rest_framework import status, generics, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404

from .models import Region, City, Product, Courier
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CourierSerializer,
    ProductSerializer,
    CitySerializer,
    RegionSerializer,
    CourierCreateSerializer,
    ProductImageSerializer,  # if needed for product images
    MyTokenObtainPairSerializer
)
from .permissions import IsAdminOrCourierBoss, IsAdmin, IsCourierBoss
from .utils import get_or_create_normalized_city, import_products_from_excel, format_text

User = get_user_model()


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# ---------------------------
# File Upload and Excel Import View
# ---------------------------
class FileUploadView(APIView):
    """
    Upload an Excel file to import Products.
    Expected Excel columns (starting at row 2):
      0: Serial Number (ignored)
      1: Order Status ("确认订单" => confirmed, else pending)
      2: Creation Date (e.g., "2025-01-06 23:59:34")
      3: Order Number
      4: Weight (string with comma as decimal separator or float)
      5: English Product Name
      6: Chinese Product Name
      7: Address
      8: City (if contains '/', use part after the slash and format it)
      9: Region (if contains '/', use part after the slash and format it)
     10: Phone Number
    """
    parser_classes = (FileUploadParser,)

    def post(self, request, *args, **kwargs):
        file_obj = request.data.get('file')
        if not file_obj:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            messages = import_products_from_excel(file_obj)
            return Response({"messages": messages}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Error processing Excel file: {e}"}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# User Registration & Authentication Endpoints
# ---------------------------
class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            tokens = get_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# ViewSets for City, Region, Courier, and Product
# ---------------------------
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class CourierViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer
    permission_classes = [IsAdminOrCourierBoss]

    def perform_create(self, serializer):
        if self.request.user.role == 'Courier Boss':
            serializer.save()


class CourierCreateAPIView(generics.CreateAPIView):
    """
    API view to create a new courier.
    """
    queryset = Courier.objects.all()
    serializer_class = CourierCreateSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrCourierBoss]

    def perform_create(self, serializer):
        if self.request.user.role == 'Courier Boss':
            courier_id = serializer.validated_data['assigned_to'].id
            courier = Courier.objects.get(id=courier_id)
            if courier.covered_cities.filter(id__in=self.request.user.courier.covered_cities.all()).exists():
                serializer.save()
            else:
                raise permissions.PermissionDenied("This courier does not cover the required city.")


class AssignProductView(APIView):
    permission_classes = [IsCourierBoss]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def home(request):
    return HttpResponse("Welcome to my Django project!")


class CourierProductListView(generics.ListAPIView):
    """
    Returns a list of Products assigned to the authenticated courier.
    Assumes that the courier is linked to the user (i.e. Courier.user).
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            # Assuming request.user is set by JWT authentication
            courier = Courier.objects.get(user=self.request.user)
        except Courier.DoesNotExist:
            return Product.objects.none()
        return Product.objects.filter(assigned_to=courier)


class ConfirmDeliveredProductView(APIView):
    """
    Endpoint for a courier to confirm delivery of a product to the customer.
    Expects a POST request with JSON:
      { "product_id": <id> }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        try:
            courier = Courier.objects.get(user=request.user)
        except Courier.DoesNotExist:
            return Response({"detail": "You are not authorized as a courier."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure product is assigned to this courier.
        if product.assigned_to != courier:
            return Response({"detail": "You are not assigned to this product."}, status=status.HTTP_403_FORBIDDEN)

        # Only allow confirming delivery if the product is already marked as Received.
        if product.order_status != "Received":
            return Response({"detail": "Product must be received first."}, status=status.HTTP_400_BAD_REQUEST)

        product.order_status = "Delivered"
        product.save()
        return Response({"detail": "Product delivery confirmed."}, status=status.HTTP_200_OK)


class ConfirmReceiptProductView(APIView):
    """
    Endpoint for a courier to confirm receipt of a product.
    Expects a POST request with JSON:
      { "product_id": <id> }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        try:
            courier = Courier.objects.get(user=request.user)
        except Courier.DoesNotExist:
            return Response({"detail": "You are not authorized as a courier."}, status=status.HTTP_403_FORBIDDEN)

        if product.assigned_to != courier:
            return Response({"detail": "You are not assigned to this product."}, status=status.HTTP_403_FORBIDDEN)

        # Update status to Received.
        product.order_status = "Received"
        product.save()
        return Response({"detail": "Product receipt confirmed."}, status=status.HTTP_200_OK)
