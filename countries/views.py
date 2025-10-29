import requests
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Country
from .serializers import CountrySerializer

class CountryViewSet(viewsets.ViewSet):
    
	@action(detail=False, methods=['post'])
	def refresh(self, request):

		# Fetch country data
		response = requests.get("https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies")
		countries_data = response.json()

		# Fetch exchange rates
		exchange_response = requests.get("https://open.er-api.com/v6/latest/USD")
		exchange_rates = exchange_response.json().get('rates', {})

		# Process each country data
		for country_data in countries_data:
		    country_name = country_data['name']
		    capital = country_data.get('capital', '')
		    region = country_data.get('region', '')
		    flag_url = country_data.get('flag', '')
		    population = country_data['population']
		    
		    # Check for currencies and get exchange rate
		    if 'currencies' in country_data and country_data['currencies']:
		        currency_code = country_data['currencies'][0]["code"]
		        exchange_rate = exchange_rates.get(currency_code, None)
		    else:
		        currency_code = None
		        exchange_rate = None

		    # Update or create the country record in the database
		    country, created = Country.objects.update_or_create(
			    name=country_name,
			    defaults={
		            'capital': capital,
		            'region': region,
		            'population': population,
		            'currency_code': currency_code,
		            'exchange_rate': exchange_rate,
		            'flag_url':  flag_url  
			        }
			)
			
		return Response({"message": "Countries refreshed successfully"}, status=status.HTTP_200_OK)


	def list(self, request):
	    queryset = Country.objects.all()
	    serializer = CountrySerializer(queryset, many=True)
	    region = self.request.query_params.get('region', None)
	    currency= self.request.query_params.get('currency', None)
	    sort = self.request.query_params.get('sort', None)

        

	    if region:
	    	queryset = queryset.filter(region=region)
	    	serializer = CountrySerializer(queryset, many=True)
	    	return Response(serializer.data)
	    if currency:
	    	queryset = queryset.filter(currency=currency)
	    	serializer = CountrySerializer(queryset, many=True)
	    	return Response(serializer.data)
	    if sort == 'gdp_desc':
	    	queryset = queryset.order_by('-estimated_gdp')  # Descending order
	    	serializer = CountrySerializer(queryset, many=True)
	    	return Response(serializer.data)
	    elif sort == 'gdp_asc':
	    	queryset = queryset.order_by('estimated_gdp')  # Ascending order
	    	serializer = CountrySerializer(queryset, many=True)
	    	return Response(serializer.data)

	    	

	    return Response(serializer.data)

       
        

	def retrieve(self, request, name=None):
	    try:
	        country = Country.objects.get(name__iexact=name)
	        serializer = CountrySerializer(country)
	        return Response(serializer.data)
	    except Country.DoesNotExist:
	        return Response({"error": "Country not found"}, status=status.HTTP_404_NOT_FOUND)

	def destroy(self, request, name=None):
	    try:
	        country = Country.objects.get(name__iexact=name)
	        country.delete()
	        return Response(status=status.HTTP_204_NO_CONTENT)
	    except Country.DoesNotExist:
	        return Response({"error": "Country not found"}, status=status.HTTP_404_NOT_FOUND)

	@action(detail=False, methods=['get'])
	def status(self, request):
	    total_countries = Country.objects.count()
	    last_refreshed_at = Country.objects.latest('last_refreshed_at').last_refreshed_at if total_countries > 0 else None
	    return Response({"total_countries": total_countries, "last_refreshed_at": last_refreshed_at})

	@action(detail=False, methods=['get'])
	def image(self, request):
	    # Logic to serve the generated summary image
	    return Response({"error": "Summary image not found"}, status=status.HTTP_404_NOT_FOUND)
