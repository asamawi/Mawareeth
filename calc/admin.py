from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter

from .models import Calculation, Person, Marriage, Heir,Deceased, Father, Mother

admin.site.register(Calculation)
admin.site.register(Marriage)

class HeirAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = Person # Optional, explicitly set here.

    # By using these `base_...` attributes instead of the regular ModelAdmin `form` and `fieldsets`,
    # the additional fields of the child models are automatically added to the admin form.
    # base_form = ...
    # base_fieldsets = (
    #     ...
    # )
    show_in_index = True
    def get_queryset(self, request):
        qs = self.model.polymorphic.get_queryset()

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        if not self.has_change_permission(request):
            qs = qs.none()

        return qs

@admin.register(Deceased)
class DeceasedAdmin(HeirAdmin):
    base_model = Deceased  # Explicitly set here!
    show_in_index = True
    # define custom features here

@admin.register(Father)
class FatherAdmin(HeirAdmin):
    base_model = Father  # Explicitly set here!
    show_in_index = True
    # define custom features here

@admin.register(Mother)
class FatherAdmin(HeirAdmin):
    base_model = Mother  # Explicitly set here!
    show_in_index = True
    # define custom features here

@admin.register(Person)
class PersonAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = Person  # Optional, explicitly set here.
    child_models = (Father, Mother, Deceased)
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.
