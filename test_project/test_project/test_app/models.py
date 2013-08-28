from django.db import models

# Create your models here.
class Promo(models.Model):
    name = models.CharField(max_length=255)
    age = models.IntegerField(null=True)


class PromoArea(models.Model):
    promo = models.ForeignKey(Promo)


