from django.http import JsonResponse
from django.shortcuts import render
from expa_data.models import ExpaApplication, SignupPerson, Opportunity
from django.db.models import Q , F, ExpressionWrapper , Count , Sum, FloatField
from django.db.models.functions import TruncMonth , Coalesce
from collections import defaultdict
from datetime import timedelta



def get_ogv_process_times(request):
    try:
        # Step 1: Get all applications for the program 'GV'
        applications = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(host_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .exclude(date_matched=None) \
            .exclude(date_approved=None)

        # SU to APP
        su_app_durations = []
        app_acc_durations = []
        acc_apd_durations = []

        for app in applications:
            if app.signuped_at and app.created_at:
                # Calculate SU to APP duration
                su_app_durations.append((app.created_at - app.signuped_at).days)
            if app.created_at and app.date_matched:
                # Calculate APP to ACC duration
                app_acc_durations.append((app.date_matched - app.created_at).days)
            if app.date_matched and app.date_approved:
                # Calculate ACC to APD duration
                acc_apd_durations.append((app.date_approved - app.date_matched).days)

        # Averages
        avg_su_app = sum(su_app_durations) / len(su_app_durations) if su_app_durations else 0
        avg_app_acc = sum(app_acc_durations) / len(app_acc_durations) if app_acc_durations else 0
        avg_acc_apd = sum(acc_apd_durations) / len(acc_apd_durations) if acc_apd_durations else 0

        return JsonResponse({
            "product": "OGV",
            "SU_to_APP_days": round(avg_su_app, 2),
            "APP_to_ACC_days": round(avg_app_acc, 2),
            "ACC_to_APD_days": round(avg_acc_apd, 2),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)





def format_timeline_data(applications, signups, programme_id):
    timeline = defaultdict(lambda: {"SU": 0, "APP": 0, "ACC": 0, "APD": 0, "REA": 0})

    for item in signups:
        month = item["month"].strftime("%Y-%m")
        timeline[month]["SU"] = item["count"]

    for ep in applications:
        if ep.created_at:
            month = ep.created_at.strftime("%Y-%m")
            timeline[month]["APP"] += 1
        if ep.date_matched:
            month = ep.date_matched.strftime("%Y-%m")
            timeline[month]["ACC"] += 1
        if ep.date_approved:
            month = ep.date_approved.strftime("%Y-%m")
            timeline[month]["APD"] += 1
        if ep.date_realized:
            month = ep.date_realized.strftime("%Y-%m")
            timeline[month]["REA"] += 1

    return sorted([
        {
            "date": month,
            "SU": data["SU"],
            "APP": data["APP"],
            "ACC": data["ACC"],
            "APD": data["APD"],
            "REA": data["REA"],
        }
        for month, data in timeline.items()
    ], key=lambda x: x["date"])

def get_ogv_timeline(request):
    try:
        timeline = defaultdict(lambda: {"SU": 0, "APP": 0, "ACC": 0, "APD": 0, "REA": 0})

        # Signups
        signups = SignupPerson.objects.exclude(
            Q(selected_programmes__icontains='8') | Q(selected_programmes__icontains='9')
        ).annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id"))

        for item in signups:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["SU"] = item["count"]

        # Applications (APP)
        applied = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(host_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id"))
        
        for item in applied:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["APP"] += item["count"]

        # Accepted (ACC)
        accepted = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(host_lc_name__iexact='Tanta') \
            .exclude(date_matched=None) \
            .annotate(month=TruncMonth("date_matched")).values("month").annotate(count=Count("id"))

        for item in accepted:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["ACC"] += item["count"]

        # Approved (APD)
        approved = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(host_lc_name__iexact='Tanta') \
            .exclude(date_approved=None) \
            .annotate(month=TruncMonth("date_approved")).values("month").annotate(count=Count("id"))

        for item in approved:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["APD"] += item["count"]

        # Realized (REA)
        realized = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(host_lc_name__iexact='Tanta') \
            .exclude(date_realized=None) \
            .annotate(month=TruncMonth("date_realized")).values("month").annotate(count=Count("id"))

        for item in realized:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["REA"] += item["count"]

        # Convert to sorted list
        timeline_list = [
            {
                "date": month,
                "SU": data["SU"],
                "APP": data["APP"],
                "ACC": data["ACC"],
                "APD": data["APD"],
                "REA": data["REA"],
            }
            for month, data in sorted(timeline.items())
        ]

        return JsonResponse({"timeline": timeline_list})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_ogv_funnel(request):
    try:
        # Filter OGV Applications (excluding Tanta as Host LC)
        base_queryset = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(host_lc_name__iexact='Tanta')

        # Count SignupPeople who are NOT GT (programme 8 or 9)
        signup_count = SignupPerson.objects.exclude(
            Q(selected_programmes__icontains='8') | Q(selected_programmes__icontains='9')
        ).count()

        data = {
            "Signups": signup_count,  # Added this
            "APP": base_queryset.count(),
            "ACC": base_queryset.exclude(date_matched=None).count(),
            "APD": base_queryset.filter(
                Q(current_status__iexact='approved') |
                Q(current_status__iexact='approval_broken') |
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "REA": base_queryset.filter(
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "FIN": base_queryset.filter(
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "COMP": base_queryset.filter(current_status__iexact='completed').count(),
        }

        return JsonResponse({"ogv_funnel": data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_ogta_funnel(request):
    try:
        # Filter OGTa Applications (exclude host LC Tanta and exclude OGV and OGTe)
        base_queryset = ExpaApplication.objects.filter(programme_id='8') \
            .exclude(host_lc_name__iexact='Tanta')

        signup_count = SignupPerson.objects.exclude(
            Q(selected_programmes__icontains='7') | Q(selected_programmes__icontains='9')
        ).count()

        data = {
            "Signups": signup_count,
            "APP": base_queryset.count(),
            "ACC": base_queryset.exclude(date_matched=None).count(),
            "APD": base_queryset.filter(
                Q(current_status__iexact='approved') |
                Q(current_status__iexact='approval_broken') |
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "REA": base_queryset.filter(
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "FIN": base_queryset.filter(
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "COMP": base_queryset.filter(current_status__iexact='completed').count(),
        }

        return JsonResponse({"ogta_funnel": data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_ogta_timeline(request):
    try:
        applications = ExpaApplication.objects.filter(programme_id=8) \
            .exclude(host_lc_name__iexact='Tanta')

        signups = SignupPerson.objects.exclude(
            Q(selected_programmes__icontains='7') | Q(selected_programmes__icontains='9')
        ).annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id"))

        timeline = format_timeline_data(applications, signups, programme_id=8)
        return JsonResponse({"timeline": timeline})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_ogta_process_times(request):
    try:
        # Step 1: Get all applications for the program 'TA'
        applications = ExpaApplication.objects.filter(programme_id=8) \
            .exclude(host_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .exclude(date_matched=None) \
            .exclude(date_approved=None)

        # SU to APP
        su_app_durations = []
        app_acc_durations = []
        acc_apd_durations = []

        for app in applications:
            if app.signuped_at and app.created_at:
                # Calculate SU to APP duration
                su_app_durations.append((app.created_at - app.signuped_at).days)
            if app.created_at and app.date_matched:
                # Calculate APP to ACC duration
                app_acc_durations.append((app.date_matched - app.created_at).days)
            if app.date_matched and app.date_approved:
                # Calculate ACC to APD duration
                acc_apd_durations.append((app.date_approved - app.date_matched).days)

        # Averages
        avg_su_app = sum(su_app_durations) / len(su_app_durations) if su_app_durations else 0
        avg_app_acc = sum(app_acc_durations) / len(app_acc_durations) if app_acc_durations else 0
        avg_acc_apd = sum(acc_apd_durations) / len(acc_apd_durations) if acc_apd_durations else 0

        return JsonResponse({
            "product": "OGTA",
            "SU_to_APP_days": round(avg_su_app, 2),
            "APP_to_ACC_days": round(avg_app_acc, 2),
            "ACC_to_APD_days": round(avg_acc_apd, 2),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_ogte_funnel(request):
    try:
        # Filter OGTe Applications (exclude host LC Tanta and exclude OGV and OGTa)
        base_queryset = ExpaApplication.objects.filter(programme_id='9') \
            .exclude(host_lc_name__iexact='Tanta')

        signup_count = SignupPerson.objects.exclude(
            Q(selected_programmes__icontains='8') | Q(selected_programmes__icontains='7')
        ).count()

        data = {
            "Signups": signup_count,
            "APP": base_queryset.count(),
            "ACC": base_queryset.exclude(date_matched=None).count(),
            "APD": base_queryset.filter(
                Q(current_status__iexact='approved') |
                Q(current_status__iexact='approval_broken') |
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "REA": base_queryset.filter(
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "FIN": base_queryset.filter(
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "COMP": base_queryset.filter(current_status__iexact='completed').count(),
        }

        return JsonResponse({"ogte_funnel": data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_ogte_timeline(request):
    try:
        applications = ExpaApplication.objects.filter(programme_id=9) \
            .exclude(host_lc_name__iexact='Tanta')

        signups = SignupPerson.objects.exclude(
            Q(selected_programmes__icontains='8') | Q(selected_programmes__icontains='7')
        ).annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id"))

        timeline = format_timeline_data(applications, signups, programme_id=9)
        return JsonResponse({"timeline": timeline})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_ogte_process_times(request):
    try:
        applications = ExpaApplication.objects.filter(programme_id=9) \
    .exclude(host_lc_name__iexact='Tanta') \
    .exclude(created_at=None) \
    .exclude(date_matched=None) \
    .exclude(date_approved=None)


        # SU to APP
        su_app_durations = []
        app_acc_durations = []
        acc_apd_durations = []

        for app in applications:
            if app.signuped_at and app.created_at:
                # Calculate SU to APP duration
                su_app_durations.append((app.created_at - app.signuped_at).days)
            if app.created_at and app.date_matched:
                # Calculate APP to ACC duration
                app_acc_durations.append((app.date_matched - app.created_at).days)
            if app.date_matched and app.date_approved:
                # Calculate ACC to APD duration
                acc_apd_durations.append((app.date_approved - app.date_matched).days)

        # Averages
        avg_su_app = sum(su_app_durations) / len(su_app_durations) if su_app_durations else 0
        avg_app_acc = sum(app_acc_durations) / len(app_acc_durations) if app_acc_durations else 0
        avg_acc_apd = sum(acc_apd_durations) / len(acc_apd_durations) if acc_apd_durations else 0

        return JsonResponse({
            "product": "OGTE",
            "SU_to_APP_days": round(avg_su_app, 2),
            "APP_to_ACC_days": round(avg_app_acc, 2),
            "ACC_to_APD_days": round(avg_acc_apd, 2),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def get_igv_funnel(request):
    try:
        # Filter IGV Applications (excluding Tanta as Home LC)
        base_queryset = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(home_lc_name__iexact='Tanta')
        data = {
            "APP": base_queryset.count(),
            "ACC": base_queryset.exclude(date_matched=None).count(),
            "APD": base_queryset.filter(
                Q(current_status__iexact='approved') |
                Q(current_status__iexact='approval_broken') |
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "REA": base_queryset.filter(
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "FIN": base_queryset.filter(
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "COMP": base_queryset.filter(current_status__iexact='completed').count(),
        }

        return JsonResponse({"igv_funnel": data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_igta_funnel(request):
    try:
        # Filter OGTa Applications (exclude host LC Tanta and exclude OGV and OGTe)
        base_queryset = ExpaApplication.objects.filter(programme_id='8') \
            .exclude(home_lc_name__iexact='Tanta')

        
        data = {
            "APP": base_queryset.count(),
            "ACC": base_queryset.exclude(date_matched=None).count(),
            "APD": base_queryset.filter(
                Q(current_status__iexact='approved') |
                Q(current_status__iexact='approval_broken') |
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "REA": base_queryset.filter(
                Q(current_status__iexact='realization_broken') |
                Q(current_status__iexact='realized') |
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "FIN": base_queryset.filter(
                Q(current_status__iexact='finished') |
                Q(current_status__iexact='completed')
            ).count(),
            "COMP": base_queryset.filter(current_status__iexact='completed').count(),
        }

        return JsonResponse({"igta_funnel": data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_igv_timeline(request):
    try:
        timeline = defaultdict(lambda: { "APP": 0, "ACC": 0, "APD": 0, "REA": 0})

       
        # Applications (APP)
        applied = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id"))
        
        for item in applied:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["APP"] += item["count"]

        # Accepted (ACC)
        accepted = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(date_matched=None) \
            .annotate(month=TruncMonth("date_matched")).values("month").annotate(count=Count("id"))

        for item in accepted:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["ACC"] += item["count"]

        # Approved (APD)
        approved = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(date_approved=None) \
            .annotate(month=TruncMonth("date_approved")).values("month").annotate(count=Count("id"))

        for item in approved:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["APD"] += item["count"]

        # Realized (REA)
        realized = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(date_realized=None) \
            .annotate(month=TruncMonth("date_realized")).values("month").annotate(count=Count("id"))

        for item in realized:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["REA"] += item["count"]

        # Convert to sorted list
        timeline_list = [
            {
                "date": month,
                "APP": data["APP"],
                "ACC": data["ACC"],
                "APD": data["APD"],
                "REA": data["REA"],
            }
            for month, data in sorted(timeline.items())
        ]

        return JsonResponse({"timeline": timeline_list})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_igta_timeline(request):
    try:
        timeline = defaultdict(lambda: { "APP": 0, "ACC": 0, "APD": 0, "REA": 0})

       
        # Applications (APP)
        applied = ExpaApplication.objects.filter(programme_id='8') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id"))
        
        for item in applied:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["APP"] += item["count"]

        # Accepted (ACC)
        accepted = ExpaApplication.objects.filter(programme_id='8') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(date_matched=None) \
            .annotate(month=TruncMonth("date_matched")).values("month").annotate(count=Count("id"))

        for item in accepted:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["ACC"] += item["count"]

        # Approved (APD)
        approved = ExpaApplication.objects.filter(programme_id='8') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(date_approved=None) \
            .annotate(month=TruncMonth("date_approved")).values("month").annotate(count=Count("id"))

        for item in approved:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["APD"] += item["count"]

        # Realized (REA)
        realized = ExpaApplication.objects.filter(programme_id='8') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(date_realized=None) \
            .annotate(month=TruncMonth("date_realized")).values("month").annotate(count=Count("id"))

        for item in realized:
            month = item["month"].strftime("%Y-%m")
            timeline[month]["REA"] += item["count"]

        # Convert to sorted list
        timeline_list = [
            {
                "date": month,
                "APP": data["APP"],
                "ACC": data["ACC"],
                "APD": data["APD"],
                "REA": data["REA"],
            }
            for month, data in sorted(timeline.items())
        ]

        return JsonResponse({"timeline": timeline_list})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_igta_slots_data(request):
    igta_data = (
        Opportunity.objects.filter(programme_short_name__iexact="GTa")
        .values("sub_product_name")
        .annotate(
            total_slots=Sum("available_slots_count") + Count(
                'slots', 
                filter=F('slots__status') == 'expired', 
                distinct=True),         
            total_applications=Sum("applicants_count"),
            total_accepted=Sum("accepted_count"),
            fulfillment=ExpressionWrapper(
                Coalesce(Sum("accepted_count"), 0.0) * 100.0 / 
                Coalesce(Sum("available_slots_count"), 1.0),  # Avoid divide by zero
                output_field=FloatField()
            )
        )
    )
    return JsonResponse(list(igta_data), safe=False)


def get_igv_slots_data(request):
    raw_data = (
        Opportunity.objects.filter(programme_short_name__iexact="GV")
        .values("sdg_target_id")
        .annotate(
            total_slots=Sum("available_slots_count") + Count(
                'slots', 
                filter=F('slots__status') == 'expired', 
                distinct=True),                     
            total_applications=Sum("applicants_count"),
            total_accepted=Sum("accepted_count"),
            fulfillment=ExpressionWrapper(
                Coalesce(Sum("accepted_count"), 0.0) * 100.0 / 
                Coalesce(Sum("available_slots_count"), 1.0),  # Avoid divide by zero
                output_field=FloatField()
            )
        )
    )

    # Rename target IDs to project names
    formatted_data = []
    for entry in raw_data:
        project_name = SDG_TARGET_NAME_MAP.get(entry["sdg_target_id"], f"Unknown ({entry['sdg_target_id']})")
        formatted_data.append({
            "project": project_name,
            "total_slots": entry["total_slots"],
            "total_applications": entry["total_applications"],
            "total_accepted": entry["total_accepted"],
            "fulfillment": entry["fulfillment"]
        })

    return JsonResponse(formatted_data, safe=False)
    


SDG_TARGET_NAME_MAP = {
    "8.6": "Skill Up",
    "3.4": "Heart Beat",
    "8.9": "On The Map",
    "13.3": "Green Leaders",
    "14.1": "Aquarica",
    "4.6": "Global Classroom",
    "4.4": "Finger Print",
    "15.5": "Rooted",
}



def get_igv_process_times(request):
    try:
        # Step 1: Get all applications for the program 'GV'
        applications = ExpaApplication.objects.filter(programme_short_name='GV') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .exclude(date_matched=None) \
            .exclude(date_approved=None)

        app_acc_durations = []
        acc_apd_durations = []

        # Step 2: Process each application to calculate durations
        for app in applications:
            app_acc_duration = None
            acc_apd_duration = None

            # Calculate APP to ACC duration
            if app.created_at and app.date_matched:
                app_acc_duration = (app.date_matched - app.created_at).days
                app_acc_durations.append(app_acc_duration)

            # Calculate ACC to APD duration
            if app.date_matched and app.date_approved:
                acc_apd_duration = (app.date_approved - app.date_matched).days
                acc_apd_durations.append(acc_apd_duration)

        # Step 3: Calculate averages
        avg_app_acc = sum(app_acc_durations) / len(app_acc_durations) if app_acc_durations else 0
        avg_acc_apd = sum(acc_apd_durations) / len(acc_apd_durations) if acc_apd_durations else 0

        # Step 4: Return the result in JSON format
        return JsonResponse({
            "product": "IGV",
            "APP_to_ACC_days": round(avg_app_acc, 2),
            "ACC_to_APD_days": round(avg_acc_apd, 2),
        })

    except Exception as e:
        # Step 5: Handle exceptions gracefully
        return JsonResponse({"error": str(e)}, status=500)


def get_igta_process_times(request):
    try:
        # Step 1: Get all applications for the program 'GV'
        applications = ExpaApplication.objects.filter(programme_short_name='GT') \
            .exclude(home_lc_name__iexact='Tanta') \
            .exclude(created_at=None) \
            .exclude(date_matched=None) \
            .exclude(date_approved=None)

        app_acc_durations = []
        acc_apd_durations = []

        # Step 2: Process each application to calculate durations
        for app in applications:
            app_acc_duration = None
            acc_apd_duration = None

            # Calculate APP to ACC duration
            if app.created_at and app.date_matched:
                app_acc_duration = (app.date_matched - app.created_at).days
                app_acc_durations.append(app_acc_duration)

            # Calculate ACC to APD duration
            if app.date_matched and app.date_approved:
                acc_apd_duration = (app.date_approved - app.date_matched).days
                acc_apd_durations.append(acc_apd_duration)

        # Step 3: Calculate averages
        avg_app_acc = sum(app_acc_durations) / len(app_acc_durations) if app_acc_durations else 0
        avg_acc_apd = sum(acc_apd_durations) / len(acc_apd_durations) if acc_apd_durations else 0

        # Step 4: Return the result in JSON format
        return JsonResponse({
            "product": "IGTa",
            "APP_to_ACC_days": round(avg_app_acc, 2),
            "ACC_to_APD_days": round(avg_acc_apd, 2),
        })

    except Exception as e:
        # Step 5: Handle exceptions gracefully
        return JsonResponse({"error": str(e)}, status=500)

# Index view
def index(request):
    return render(request, 'OGX.html')
def ICX(request):
    return render(request, 'ICX.html')
def dashboard(request):
    return render (request, 'Dashboard.html')

