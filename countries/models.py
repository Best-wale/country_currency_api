from django.db import models
import random

class Country(models.Model):
    name = models.CharField(max_length=100)
    capital = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    population = models.BigIntegerField()
    currency_code = models.CharField(max_length=10,blank=True, null=True)
    exchange_rate = models.FloatField(blank=True, null=True)
    estimated_gdp = models.FloatField(blank=True, null=True)
    flag_url = models.URLField(blank=True, null=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.exchange_rate:
            multiplier = random.randint(1000, 2000)
            self.estimated_gdp = self.population * multiplier / self.exchange_rate
        else:
            self.estimated_gdp = 0
        super().save(*args, **kwargs)
    def __str__(self):
    	return self.name
