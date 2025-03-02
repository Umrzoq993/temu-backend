from django.contrib.admin import AdminSite


class MyAdminSite(AdminSite):
    site_header = "My Project Administration"
    site_title = "My Admin"
    index_title = "Welcome to My Admin"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)

        if request.user.is_authenticated and request.user.role == "Courier Boss":
            filtered_app_list = []
            for app in app_list:
                # Filter models to only include the Courier model
                filtered_models = [
                    model for model in app.get('models', [])
                    if model.get('object_name', '') == 'Courier'
                ]
                print("Filtered models for app:", app['app_label'], filtered_models)  # Debug: Print filtered models
                if filtered_models:
                    # Create a new app dictionary with only the Courier model
                    new_app = app.copy()
                    new_app['models'] = filtered_models
                    filtered_app_list.append(new_app)
            print("Final filtered_app_list:", filtered_app_list)  # Debug: Print the final filtered app list
            return filtered_app_list

        # For non-operator users, return the full app list
        return app_list


# Instantiate the custom admin site
admin_site = MyAdminSite(name='myadmin')
