# Create your views here.

from rest_framework import generics
from test_project.test_app.models import Promo


class APIPromoSingleView(generics.RetrieveAPIView):
    model = Promo

class APIPromoListView(generics.ListAPIView):
    model = Promo



