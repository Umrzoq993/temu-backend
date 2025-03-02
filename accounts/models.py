from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from datetime import date


class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Viloyat (shahar)"  # Singular
        verbose_name_plural = "Viloyatlar (shaharlar)"  # Plural


class City(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="cities")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Shahar (tuman)"  # Singular
        verbose_name_plural = "Shaharlar (tumanlar)"  # Plural


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')
        extra_fields.setdefault('is_staff', True)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, choices=[('Admin', 'Admin'), ('Operator', 'Operator')])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'role']

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Foydalanuvchi"  # Singular
        verbose_name_plural = "Foydalanuvchilar"  # Plural


class Courier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    covered_cities = models.ManyToManyField(City)
    plain_password = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.full_name

    class Meta:
        verbose_name = "Kuryer"  # Singular
        verbose_name_plural = "Kuryerlar"  # Plural


class Product(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(default=date.today)
    order_number = models.CharField(max_length=50, unique=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2)  # in kilograms
    address = models.CharField(max_length=255)
    region = models.ForeignKey('Region', on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=15)
    order_status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Dispatched', 'Dispatched'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    ], default="pending")
    assigned_to = models.ForeignKey('Courier', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.order_number}"

    class Meta:
        verbose_name = "Pochta"  # Singular
        verbose_name_plural = "Pochtalar"  # Plural


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.order_number}"

    class Meta:
        verbose_name = "Pochta rasmi"
        verbose_name_plural = "Pochta rasmlari"