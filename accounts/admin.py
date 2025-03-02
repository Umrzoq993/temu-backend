from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.utils.html import format_html
from .forms import CourierCreationForm, ProductForm, ExcelImportForm
from .utils import import_products_from_excel
from .models import User, Region, City, Courier, Product, ProductImage
from .filter import AssignedFilter

# Import custom admin site
from accounts.admin_site import admin_site


# Custom User Admin
@admin.register(User, site=admin_site)
class CustomUserAdmin(UserAdmin):
    list_per_page = 20
    model = User
    list_display = ['username', 'full_name', 'role', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
        ('Advanced options', {'classes': ('collapse',), 'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'full_name', 'role', 'is_active', 'is_staff'),
        }),
    )
    search_fields = ('username',)
    ordering = ('username',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(role="Courier")


# Region Admin
@admin.register(Region, site=admin_site)
class RegionAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ['name']
    search_fields = ['name']


# City Admin
@admin.register(City, site=admin_site)
class CityAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ['name', 'region']
    list_filter = ['region']
    search_fields = ['name']
    autocomplete_fields = ['region']


# Courier Admin
@admin.register(Courier, site=admin_site)
class CourierAdmin(admin.ModelAdmin):
    list_per_page = 20
    add_form = CourierCreationForm
    list_display = ['user__full_name', 'custom_user', 'custom_password', 'display_covered_cities']
    search_fields = ['user__username']
    filter_horizontal = ['covered_cities']

    @admin.display(description="F.I.Sh.")
    def custom_full_name(self, obj):
        return obj.user__full_name

    @admin.display(description="Foydalanuvchi nomi")
    def custom_user(self, obj):
        return obj.user

    @admin.display(description="Foydalanuvchi paroli")
    def custom_password(self, obj):
        return obj.plain_password

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            form_class = self.get_form(request)
            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                new_object = form.save(commit=False)
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                generated_password = form.generated_password
                self.message_user(
                    request,
                    f"Courier created successfully. Generated password: {generated_password}",
                    level=messages.SUCCESS
                )
                return self.response_add(request, new_object)
        return super().add_view(request, form_url, extra_context)

    def display_covered_cities(self, obj):
        return ", ".join([city.name for city in obj.covered_cities.all()])

    display_covered_cities.short_description = 'Javobgarlik hududlari'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Adjust the number of extra forms if needed


# Product Admin
@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_per_page = 20
    form = ProductForm
    change_list_template = "admin/products/product_change_list.html"
    list_display = [
        'order_number',
        'order_status',
        'city',
        'region',
        'assigned_to',  # Uses our DAL widget from ProductForm
        'latitude',
        'longitude',
    ]
    list_filter = ['order_status', 'region', 'city', AssignedFilter]
    search_fields = ['order_number', 'name']
    list_editable = ['order_status', 'assigned_to']
    fields = (
        'name',
        'date',
        'order_number',
        'weight',
        'region',
        'city',
        'phone_number',
        'assigned_to',
        'latitude',
        'longitude',
    )
    raw_id_fields = ('city', 'region')  # Note: Do not include assigned_to here so that the DAL widget is used.
    inlines = [ProductImageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If the logged-in user is a courier, filter the products
        if request.user.role == "Courier":
            qs = qs.filter(assigned_to__user=request.user)
        return qs

    def get_readonly_fields(self, request, obj=None):
        # If the user is an operator, allow editing only of assigned_to.
        if request.user.role == "Operator":
            # Mark all model fields as readonly except 'assigned_to'
            model_fields = [f.name for f in self.model._meta.fields]
            return tuple(field for field in model_fields if field != "assigned_to")
        return super().get_readonly_fields(request, obj)

    def get_changelist_form(self, request, **kwargs):
        return self.form

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel), name='product_upload_excel'),
        ]
        return custom_urls + urls

    def import_excel(self, request):
        if request.method == "POST":
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = form.cleaned_data["excel_file"]
                result_messages = import_products_from_excel(excel_file)
                self.message_user(request, "Import completed: " + " ".join(result_messages))
                return redirect("..")
        else:
            form = ExcelImportForm()
        context = dict(
            self.admin_site.each_context(request),
            form=form,
        )
        return render(request, "admin/products/import_excel.html", context)

    def assigned_to_display(self, obj):
        if obj.assigned_to:
            return format_html(
                '<a href="{}">{}</a>',
                reverse("admin:accounts_courier_change", args=(obj.assigned_to.pk,)),
                obj.assigned_to.user.username
            )
        return "-"

    def changelist_view(self, request, extra_context=None):
        """
        Override the changelist view to perform a partial save when the form is submitted.
        If one row fails to save, the others are still saved.
        """
        if request.method == 'POST':
            # Get the standard response from the parent change list view.
            response = super().changelist_view(request, extra_context)
            try:
                # The ChangeList instance is available in context_data.
                cl = response.context_data['cl']
                formset = cl.formset
            except (AttributeError, KeyError):
                return response

            saved_count = 0
            error_messages = {}
            # Process each form in the formset individually.
            for form in formset.forms:
                # Only process forms that have changes.
                if form.has_changed():
                    if form.is_valid():
                        try:
                            form.save()
                            saved_count += 1
                        except Exception as e:
                            error_messages[form.prefix] = str(e)
                    else:
                        error_messages[form.prefix] = form.errors.as_json()
            if error_messages:
                self.message_user(request, f"Some rows had errors: {error_messages}", level=messages.ERROR)
            if saved_count:
                self.message_user(request, f"Successfully saved {saved_count} row(s).", level=messages.SUCCESS)
            # Redirect back to the change list page
            return redirect(request.get_full_path())
        return super().changelist_view(request, extra_context)

    assigned_to_display.short_description = "Assigned Courier"
