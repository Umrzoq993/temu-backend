from django.contrib.admin import SimpleListFilter


class AssignedFilter(SimpleListFilter):
    title = "Kuryerga biriktirilganlik"  # Display title
    parameter_name = "assigned"  # URL query parameter

    def lookups(self, request, model_admin):
        return (
            ('assigned', 'Biriktirilgan'),
            ('unassigned', 'Biriktirilmagan'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'assigned':
            return queryset.filter(assigned_to__isnull=False)
        if self.value() == 'unassigned':
            return queryset.filter(assigned_to__isnull=True)
        return queryset
