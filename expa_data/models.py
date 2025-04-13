import uuid
from django.db import models

class ExpaApplication(models.Model):
    ep_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    current_status = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(null=True, blank=True)
    signuped_at = models.DateTimeField(null=True, blank=True)
    date_matched = models.DateTimeField(null=True, blank=True)  # Added
    date_approved = models.DateTimeField(null=True, blank=True)  # Added
    date_realized = models.DateTimeField(null=True, blank=True)  # Added
    experience_end_date = models.DateField(null=True, blank=True)  # Removed max_length
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    profile_photo = models.URLField(blank=True, null=True)
    home_lc_name = models.CharField(max_length=255, null=True, blank=True)
    home_mc_name = models.CharField(max_length=255, null=True, blank=True)
    opportunity_title = models.CharField(max_length=255, null=True, blank=True)
    opportunity_duration = models.CharField(max_length=255, null=True, blank=True)
    opportunity_earliest_start_date = models.DateField(null=True, blank=True)  # Removed max_length
    opportunity_latest_end_date = models.DateField(null=True, blank=True)  # Removed max_length
    programme_short_name = models.CharField(max_length=255, null=True, blank=True)
    programme_id = models.CharField(max_length=255, null=True, blank=True)
    home_lc_name_opportunity = models.CharField(max_length=255, null=True, blank=True)
    home_mc_name_opportunity = models.CharField(max_length=255, null=True, blank=True)
    host_lc_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'expa_data_application'


class SignupPerson(models.Model):
    ep_id = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    profile_photo = models.URLField(blank=True, null=True)
    home_lc_name = models.CharField(max_length=255, null=True, blank=True)
    home_mc_name = models.CharField(max_length=255, null=True, blank=True)
    selected_programmes = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'expa_data_signup_person'

    def __str__(self):
        return self.full_name
    

class Opportunity(models.Model):
    expa_id = models.CharField(max_length=50, unique=True)  # Opportunity ID from EXPA
    title = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    date_opened = models.DateTimeField(null=True, blank=True)

    applicants_count = models.IntegerField(default=0)
    accepted_count = models.IntegerField(default=0)

    programme_short_name = models.CharField(max_length=50, null=True, blank=True)
    sub_product_name = models.CharField(max_length=100, null=True, blank=True)

    sdg_target_id = models.CharField(max_length=20, null=True, blank=True)

    # Store slot IDs and available_slot IDs as JSON arrays (can be converted to relations later if needed)
    slots = models.JSONField(null=True, blank=True)
    available_slots_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.expa_id})"

