import requests
from django.http import JsonResponse
from .models import ExpaApplication, SignupPerson ,Opportunity  
from django.shortcuts import render
from django.db.models import Count
from collections import Counter
from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_datetime



# Sync EXPA data (applications)
def sync_expa_data(request):
    url = "https://gis-api.aiesec.org/graphql"

    headers = {
        "Authorization": "NjsAZUESIfw5ej4r9UjyzG8ApqL8BukU2BLh-Abp9Cc",  # Use your token
        "Content-Type": "application/json"
    }

    # Updated GraphQL query with date filters
    query = """
    query {
      allOpportunityApplication(
        page: 1,
        per_page: 1000,
        filters: {
          created_at: {
            from: "2024-02-01",
            to: "2025-1-31"
          }
        }
      ) {
        data {
          id
          status
          current_status
          created_at
          date_matched       
          date_approved      
          date_realized      
          experience_end_date
          person {
            id
            full_name
            email
            created_at
            profile_photo
            home_lc {
              id
              name
            }
            home_mc {
              id
              name
            }
          }
          opportunity {
            id
            title
            duration
            earliest_start_date
            latest_end_date
            programme {
              id
              short_name
            }
            home_lc {
              id
              name
            }
            home_mc {
              id
              name
            }
            host_lc {
              id
              name
            }
          }
        }
      }
    }
    """

    response = requests.post(url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("Response Data:", data)
        applications = data.get('data', {}).get('allOpportunityApplication', {}).get('data', [])

        for app in applications:
            print("Processing Application:", app)

            # Parse dates safely, set to None if not present
            created_at = None
            experience_end_date = None
            date_matched = None
            date_approved = None
            date_realized = None

            # Parse date_matched
            if app.get('date_matched'):
                try:
                    matched_naive = datetime.fromisoformat(app['date_matched'].replace("Z", "+00:00")).date()
                    date_matched = timezone.make_aware(datetime.combine(matched_naive, datetime.min.time()))
                except Exception as e:
                    print(f"Invalid date_matched format: {app['date_matched']}, Error: {e}")
            # Parse date_approved
            if app.get('date_approved'):
                try:
                    approved_naive = datetime.fromisoformat(app['date_approved'].replace("Z", "+00:00")).date()
                    date_approved = timezone.make_aware(datetime.combine(approved_naive, datetime.min.time()))
                except Exception as e:
                    print(f"Invalid date_approved format: {app['date_approved']}, Error: {e}")
            # Parse date_realized
            if app.get('date_realized'):
                try:
                    realized_naive = datetime.fromisoformat(app['date_realized'].replace("Z", "+00:00")).date()
                    date_realized = timezone.make_aware(datetime.combine(realized_naive, datetime.min.time()))
                except Exception as e:
                    print(f"Invalid date_realized format: {app['date_realized']}, Error: {e}")
            # Parse created_at
            if app.get('created_at'):
                try:
                    created_at_naive = datetime.fromisoformat(app['created_at'].replace("Z", "+00:00")).date()
                    created_at = timezone.make_aware(datetime.combine(created_at_naive, datetime.min.time()))
                except Exception as e:
                    print(f"Invalid created_at format: {app['created_at']}, Error: {e}")
            # Parse experience_end_date
            if app.get('experience_end_date'):
                try:
                    experience_end_date_naive = datetime.fromisoformat(app['experience_end_date'].replace("Z", "+00:00")).date()
                    experience_end_date = timezone.make_aware(experience_end_date_naive)
                except Exception as e:
                    print(f"Invalid experience_end_date format: {app['experience_end_date']}, Error: {e}")

            # Update or create the application record in the database
            ExpaApplication.objects.update_or_create(
                ep_id=app['id'],
                defaults={
                    'status': app['status'],
                    'current_status': app['current_status'],
                    'created_at': created_at,
                    'signuped_at': app['person']['created_at'],
                    'experience_end_date': experience_end_date,
                    'date_matched': date_matched,
                    'date_approved': date_approved,
                    'date_realized': date_realized,
                    'full_name': app['person']['full_name'],
                    'email': app['person']['email'],
                    'profile_photo': app['person'].get('profile_photo', ''),
                    'home_lc_name': app['person']['home_lc']['name'],
                    'home_mc_name': app['person']['home_mc']['name'],
                    'opportunity_title': app['opportunity']['title'],
                    'opportunity_duration': app['opportunity']['duration'],
                    'opportunity_earliest_start_date': app['opportunity']['earliest_start_date'],
                    'opportunity_latest_end_date': app['opportunity']['latest_end_date'],
                    'programme_short_name': app['opportunity']['programme']['short_name'],
                    'programme_id': app['opportunity']['programme']['id'],
                    'home_lc_name_opportunity': app['opportunity']['home_lc']['name'],
                    'home_mc_name_opportunity': app['opportunity']['home_mc']['name'],
                    'host_lc_name': app['opportunity']['host_lc']['name'] if app['opportunity'].get('host_lc') else ''
                }
            )

            print(f"Inserted/Updated: {app['id']}")

        return JsonResponse({"status": "Data synced successfully"})
    else:
        return JsonResponse({"error": "Failed to fetch data from EXPA", "details": response.text})


# Funnel Dashboard (for tracking status counts)
def funnel_dashboard(request):
    funnel_data = ExpaApplication.objects.values('status').annotate(count=Count('id'))
    status_counts = dict(Counter(ExpaApplication.objects.values_list("status", flat=True)))

    context = {
        'funnel_data': funnel_data
    }
    return render(request, "expa_data/applications_list.html", {"funnel_data": status_counts})


# Sync Signup People
def sync_signup_people(request):
    url = "https://gis-api.aiesec.org/graphql"
    headers = {
        "Authorization": "T-FpUyziE1oEtoOjgof4pHuOMt8oZyNriLPsOH2RjZc",  # Use your token
        "Content-Type": "application/json"
    }

    query = """
query {
  people(page: 1,
    per_page: 1000) {
    data {
      id
      full_name
      email
      created_at
      profile_photo
      home_lc {
        id
        name
      }
      home_mc {
        id
        name
      }
      person_profile {
        selected_programmes
      }
    }
  }
}
"""

    response = requests.post(url, json={'query': query}, headers=headers)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    if response.status_code == 200:
        people = response.json().get("data", {}).get("people", {}).get("data", [])
        print("Fetched People:", people)

        for person in people:
            created_at = None
            try:
                 if person.get('created_at'):
                    created_at = parse_datetime(person['created_at'])  # This handles timezone too
            except Exception as e:

             print(f"[ERROR] Could not parse created_at for person ID {person['id']}: {e}")

            SignupPerson.objects.update_or_create(
                ep_id=person['id'],
                defaults={
                    'full_name': person['full_name'],
                    'email': person['email'],
                    'created_at': created_at,
                    'profile_photo': person.get('profile_photo'),
                    'home_lc_name': person['home_lc']['name'] if person.get('home_lc') else '',
                    'home_mc_name': person['home_mc']['name'] if person.get('home_mc') else '',
                    'selected_programmes': ", ".join(str(programme) for programme in person.get('person_profile', {}).get('selected_programmes', []))
                }
            )

        return JsonResponse({"status": "Signup people synced successfully"})
    else:
        return JsonResponse({"error": "Failed to fetch signup people", "details": response.text})
     


def sync_expa_opportunities(request):
    url = "https://gis-api.aiesec.org/graphql"

    headers = {
        "Authorization": "zrbn3XtUBh2yILDdZImfOMIdVkqSIw3DN4wxOX4x1pQ",  # Replace with your valid token
        "Content-Type": "application/json"
    }

    query = """
    query {
      opportunities(
        filters: { 
          date_opened: { from: "2024-02-01" } 
        }
        per_page: 100
      ) {
        data {
          id
          title
          status
          created_at
          date_opened
          applicants_count
          accepted_count
          slots {
            id
            status
          }
          programme {
            short_name_display
          }
          sub_product {
            name
          }
          available_slots {
            id
          }
          sdg_info {
            sdg_target {
              target_id
            }
          }
        }
      }
    }
    """

    response = requests.post(url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("Raw Opportunity Data:", data)

        opportunities = data.get("data", {}).get("opportunities", {}).get("data", [])

        for opp in opportunities:
            # Parse dates
            created_at = parse_date(opp.get('created_at'))
            date_opened = parse_date(opp.get('date_opened'))

            # Extract nested data
            programme_short_name = opp.get('programme', {}).get('short_name_display', '')
            sub_product = opp.get('sub_product') or {}
            sub_product_name = sub_product.get('name', '')
            sdg_info = opp.get('sdg_info') or {}
            sdg_target = sdg_info.get('sdg_target') or {}
            sdg_target_id = sdg_target.get('target_id', '')
            slots = opp.get('slots', [])
            available_slots_count = len(opp.get('available_slots') or [])
 
            # Save to DB
            Opportunity.objects.update_or_create(
                expa_id=opp.get('id'),
                defaults={
                    'title': opp.get('title', ''),
                    'status': opp.get('status', ''),
                    'created_at': created_at,
                    'date_opened': date_opened,
                    'applicants_count': opp.get('applicants_count', 0),
                    'accepted_count': opp.get('accepted_count', 0),
                    'programme_short_name': programme_short_name,
                    'sub_product_name': sub_product_name,
                    'sdg_target_id': sdg_target_id,
                    'slots': slots,
                    'available_slots_count': available_slots_count
                }
            )

            print(f"Synced Opportunity: {opp.get('id')}")

        return JsonResponse({"status": "Opportunity data synced successfully."})
    else:
        return JsonResponse({"error": "Failed to fetch opportunities", "details": response.text})


def parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return timezone.make_aware(dt)
    except Exception as e:
        print(f"Date parsing error: {e}")
        return None
