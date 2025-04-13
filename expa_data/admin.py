from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ExpaApplication, SignupPerson, Opportunity

# Custom filter to exclude Tanta from home_lc_name
class ExcludeTantaHomeLCFilter(admin.SimpleListFilter):
    title = _('Exclude Tanta from Home LC')  # The title of the filter in the sidebar
    parameter_name = 'exclude_home_tanta'  # The parameter name in the URL query string

    def lookups(self, request, model_admin):
        # The options for this filter
        return (
            ('exclude_home_tanta', _('Exclude Tanta from Home LC')),  # Show option to exclude Tanta from Home LC
        )

    def queryset(self, request, queryset):
        # The logic that applies the filter
        if self.value() == 'exclude_home_tanta':
            return queryset.exclude(home_lc_name__iexact='Tanta')
        return queryset

# Custom filter to exclude Tanta from host_lc_name
class ExcludeTantaHostLCFilter(admin.SimpleListFilter):
    title = _('Exclude Tanta from Host LC')  # The title of the filter in the sidebar
    parameter_name = 'exclude_host_tanta'  # The parameter name in the URL query string

    def lookups(self, request, model_admin):
        # The options for this filter
        return (
            ('exclude_host_tanta', _('Exclude Tanta from Host LC')),  # Show option to exclude Tanta from Host LC
        )

    def queryset(self, request, queryset):
        # The logic that applies the filter
        if self.value() == 'exclude_host_tanta':
            return queryset.exclude(host_lc_name__iexact='Tanta')
        return queryset

class ExpaApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'status', 'current_status', 'created_at', 'home_lc_name', 'host_lc_name')
    list_filter = ('created_at', 'current_status', 'home_lc_name', 'host_lc_name', 'programme_short_name','programme_id',
                   ExcludeTantaHomeLCFilter, ExcludeTantaHostLCFilter)  # Add both custom filters here
    date_hierarchy = 'created_at'
    search_fields = ('full_name', 'email', 'status', 'current_status','programme_short_name')

# Register the model with the custom admin class
admin.site.register(ExpaApplication, ExpaApplicationAdmin)

from .models import SignupPerson

@admin.register(SignupPerson)
class SignupPersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'created_at', 'home_lc_name', 'home_mc_name','selected_programmes')
    list_filter = ('created_at', 'home_lc_name', 'home_mc_name', 'selected_programmes',ExcludeTantaHomeLCFilter)
    date_hierarchy = 'created_at'
    search_fields = ('full_name', 'email', 'home_lc_name', 'home_mc_name','selected_programmes')

# Custom filter for 'status' field in Opportunity
class OpportunityStatusFilter(admin.SimpleListFilter):
    title = _('Opportunity Status')  # The title of the filter in the sidebar
    parameter_name = 'status'  # The parameter name in the URL query string

    def lookups(self, request, model_admin):
        # The options for this filter
        return (
            ('open', _('Open')),  # Show option to filter opportunities with 'Open' status
            ('closed', _('Closed')),  # Show option to filter opportunities with 'Closed' status
        )

    def queryset(self, request, queryset):
        # The logic that applies the filter
        if self.value() == 'open':
            return queryset.filter(status='open')
        elif self.value() == 'closed':
            return queryset.filter(status='closed')
        return queryset

# Admin configuration for Opportunity model
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'status', 'created_at', 'date_opened', 'applicants_count', 'accepted_count',
        'programme_short_name', 'sub_product_name', 'sdg_target_id'
    )
    list_filter = (
        'status', 'programme_short_name', 'sub_product_name', OpportunityStatusFilter  # Add custom filter here (class object)
    )
    date_hierarchy = 'created_at'
    search_fields = ('title', 'status', 'programme_short_name', 'sub_product_name')

# Register the Opportunity model with the custom admin class
admin.site.register(Opportunity, OpportunityAdmin)
