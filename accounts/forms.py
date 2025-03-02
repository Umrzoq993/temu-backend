import string
from django import forms
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from dal import autocomplete
from .models import Courier, City, Product
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(label="Select Excel file")


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'assigned_to': autocomplete.ModelSelect2(
                url='courier-autocomplete',
                forward=['city'],  # Simply pass a list of field names
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing an existing product with a city, filter assigned_to.
        if self.instance and self.instance.pk and self.instance.city:
            if 'assigned_to' in self.fields:
                self.fields['assigned_to'].queryset = Courier.objects.filter(
                    covered_cities=self.instance.city
                )


def generate_valid_password(length=12, max_attempts=100):
    # Use only letters and digits
    allowed_chars = string.ascii_letters + string.digits
    for attempt in range(max_attempts):
        password = get_random_string(length, allowed_chars)
        try:
            validate_password(password)
            return password
        except ValidationError:
            continue
    raise Exception("Failed to generate a valid password after {} attempts".format(max_attempts))


class CourierCreationForm(forms.ModelForm):
    # Fields for creating the related User
    username = forms.CharField(label="Username", required=True)
    full_name = forms.CharField(label="Full Name", required=True)

    # Courier-specific field(s)
    covered_cities = forms.ModelMultipleChoiceField(
        queryset=City.objects.all(),
        required=True,
        label="Covered Cities"
    )
    # Optionally, add a region field to filter cities
    region = forms.ModelChoiceField(queryset=None, label="Region", required=True)

    class Meta:
        model = Courier
        # region is used only to filter covered_cities in the form; it's not stored on Courier.
        fields = ['region', 'covered_cities']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate region queryset (assuming Region model exists)
        from .models import Region  # local import to avoid circular import issues
        self.fields['region'].queryset = Region.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        if region:
            # Filter covered_cities to only those belonging to the selected region.
            self.fields['covered_cities'].queryset = self.fields['covered_cities'].queryset.filter(region=region)
        return cleaned_data

    def save(self, commit=True):
        generated_password = generate_valid_password()
        self.generated_password = generated_password  # Store for later reference.
        username = self.cleaned_data.get("username")
        full_name = self.cleaned_data.get("full_name")

        # Create the associated user with is_staff=True so they can log into admin.
        user = User.objects.create_user(
            username=username,
            password=generated_password,
            full_name=full_name,
            role="Courier",  # Adjust role if needed.
            is_staff=True
        )

        # Grant the courier permission to view products.
        content_type = ContentType.objects.get_for_model(Product)
        view_permission = Permission.objects.get(content_type=content_type, codename='view_product')
        user.user_permissions.add(view_permission)

        # Create the Courier instance and link it to the new user.
        courier = super().save(commit=False)
        courier.user = user
        # Save the generated password for display purposes.
        courier.plain_password = generated_password
        if commit:
            courier.save()
            self.save_m2m()
        return courier
