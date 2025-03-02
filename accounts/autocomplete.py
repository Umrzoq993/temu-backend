from dal import autocomplete
from .models import Courier


class CourierAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Courier.objects.all()
        city_id = self.forwarded.get('city')
        try:
            city_id = int(city_id)
        except (TypeError, ValueError):
            city_id = None
        if city_id:
            qs = qs.filter(covered_cities__id=city_id)
        return qs

