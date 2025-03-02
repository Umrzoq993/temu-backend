from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Courier, Product, Region, City, ProductImage
from .forms import CourierCreationForm
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claim: 'role' from the user instance.
        token['role'] = user.role  # Make sure your User model has a field "role"
        return token


class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']


class CitySerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), source='region', write_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'region', 'region_id']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'full_name', 'role')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'full_name', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CourierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = '__all__'


class CourierCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    full_name = serializers.CharField(max_length=255)
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())
    covered_cities = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), many=True)

    # Optionally, you can include read-only plain_password in the output:
    plain_password = serializers.CharField(read_only=True)

    def create(self, validated_data):
        # Build data dictionary to pass to the CourierCreationForm.
        form_data = {
            'username': validated_data.get('username'),
            'full_name': validated_data.get('full_name'),
            'region': validated_data.get('region').id,
            # The form expects the region; you might need to pass the ID or instance depending on your form.
            # covered_cities will be a list of City IDs.
            'covered_cities': [city.id for city in validated_data.get('covered_cities')],
        }
        # Instantiate the form with form_data. Note: You might need to convert data to strings if required.
        form = CourierCreationForm(data=form_data)
        if form.is_valid():
            courier = form.save()
            return courier
        else:
            raise serializers.ValidationError(form.errors)

    def to_representation(self, instance):
        # Customize output: return courier ID and generated plain password.
        return {
            "id": instance.id,
            "plain_password": instance.plain_password,
            "username": instance.user.username,
            "full_name": instance.user.full_name,
            "covered_cities": [city.id for city in instance.covered_cities.all()],
            "region": instance.covered_cities.first().region.id if instance.covered_cities.exists() else None,
        }


class ProductSerializer(serializers.ModelSerializer):
    region_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'date',
            'order_number',
            'weight',
            'address',
            'region',
            'city',
            'phone_number',
            'order_status',
            'assigned_to',
            'region_name',
            'city_name',
        ]

    def get_region_name(self, obj):
        return obj.region.name if obj.region else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None

    def validate(self, data):
        """
        Check that the courier covers the city of the product.
        """
        courier = data.get('assigned_to')
        product_city = data.get('city')

        if courier and product_city:
            if not courier.covered_cities.filter(id=product_city.id).exists():
                raise serializers.ValidationError(
                    "The assigned courier does not cover the delivery city of the product.")

        return data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'caption']
