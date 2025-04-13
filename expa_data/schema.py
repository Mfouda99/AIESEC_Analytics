import graphene
from graphene_django.types import DjangoObjectType
from .models import ExpaApplication, SignupPerson, Opportunity

class ExpaApplicationType(DjangoObjectType):
    class Meta:
        model = ExpaApplication
        fields = ('id', 'name', 'email')  # These fields match the model

class SignupPersonType(DjangoObjectType):
    class Meta:
        model = SignupPerson
        fields = (
            'id',
            'person_id',
            'full_name',
            'email',
            'created_at',
            'profile_photo',
            'home_lc_name',
            'home_mc_name',
            'selected_programmes'
        )

class OpportunityType(DjangoObjectType):
    class Meta:
        model = Opportunity
        fields = (
            'id', 
            'expa_id', 
            'title', 
            'status', 
            'created_at', 
            'date_opened', 
            'applicants_count', 
            'accepted_count', 
            'programme_short_name', 
            'sub_product_name', 
            'sdg_target_id', 
            'slots', 
            'available_slots'
        )

class Query(graphene.ObjectType):
    expa_applications = graphene.List(ExpaApplicationType)
    signup_people = graphene.List(SignupPersonType)

    def resolve_expa_applications(self, info):
        return ExpaApplication.objects.all()

    def resolve_signup_people(self, info):
        return SignupPerson.objects.all()
    def resolve_opportunities(self, info):
        return Opportunity.objects.all()

class Mutation(graphene.ObjectType):
    # Add mutations if needed later
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
