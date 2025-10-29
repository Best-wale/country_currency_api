import io
import random
import requests
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from .models import Country

JSON_MIME = "application/json"

# Helpers
def _iso(dt):
    return dt.isoformat() if dt is not None else None

def _get_exchange_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        r.raise_for_status()
        return r.json().get("rates", {}) or {}
    except requests.RequestException:
        return {}

def _fetch_countries_data():
    try:
        r = requests.get(
            "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies",
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

# POST /countries/refresh/
@csrf_exempt
@require_http_methods(["POST"])
def refresh_countries(request):
    countries_data = _fetch_countries_data()
    if countries_data is None:
        return JsonResponse({"error": "Failed to fetch countries source"}, status=502)

    exchange_rates = _get_exchange_rates()

    refreshed_count = 0
    timestamp = now()

    for c in countries_data:
        name = c.get("name")
        if not name:
            continue

        capital = c.get("capital") or ""
        region = c.get("region") or ""
        population = c.get("population") or 0
        flag_url = c.get("flag") or ""

        currency_code = None
        if c.get("currencies"):
            first_cur = c["currencies"][0]
            code = first_cur.get("code")
            if code:
                currency_code = code.upper()

        exchange_rate = None
        if currency_code:
            # try both upper and as-is
            exchange_rate = exchange_rates.get(currency_code) or exchange_rates.get(currency_code.upper())

        if exchange_rate in (0, "0"):
            exchange_rate = None

        multiplier = random.randint(1000, 2000)
        if exchange_rate:
            try:
                estimated_gdp = population * multiplier / float(exchange_rate)
            except Exception:
                estimated_gdp = population * multiplier
        else:
            estimated_gdp = population * multiplier

        # Save/update model (assumes `name` is unique or use update_or_create)
        Country.objects.update_or_create(
            name=name,
            defaults={
                "capital": capital,
                "region": region,
                "population": population,
                "currency_code": currency_code,
                "exchange_rate": exchange_rate,
                "flag_url": flag_url,
                "estimated_gdp": estimated_gdp,
                "last_refreshed_at": timestamp,
            },
        )
        refreshed_count += 1

    return JsonResponse(
        {
            "message": "Countries refreshed",
            "refreshed_count": refreshed_count,
            "last_refreshed_at": _iso(timestamp),
        },
        status=200,
    )

# GET /countries/
@require_http_methods(["GET"])
def list_countries(request):
    qs = Country.objects.all()
    region = request.GET.get("region")
    currency = request.GET.get("currency")
    sort = request.GET.get("sort")

    if region:
        qs = qs.filter(region__iexact=region)
    if currency:
        qs = qs.filter(currency_code__iexact=currency)

    if sort == "gdp_desc":
        qs = qs.order_by("-estimated_gdp")
    elif sort == "gdp_asc":
        qs = qs.order_by("estimated_gdp")

    data = []
    for c in qs:
        data.append(
            {
                "name": c.name,
                "capital": c.capital,
                "region": c.region,
                "population": c.population,
                "currency_code": c.currency_code,
                "exchange_rate": c.exchange_rate,
                "flag_url": c.flag_url,
                "estimated_gdp": c.estimated_gdp,
                "last_refreshed_at": _iso(c.last_refreshed_at),
            }
        )
    return JsonResponse(data, safe=False, status=200)

# GET /countries/<name>/
@require_http_methods(["GET"])
def get_country(request, name):
    country = Country.objects.filter(name__iexact=name).first()
    if not country:
        return JsonResponse({"error": "Country not found"}, status=404)
    data = {
        "name": country.name,
        "capital": country.capital,
        "region": country.region,
        "population": country.population,
        "currency_code": country.currency_code,
        "exchange_rate": country.exchange_rate,
        "flag_url": country.flag_url,
        "estimated_gdp": country.estimated_gdp,
        "last_refreshed_at": _iso(country.last_refreshed_at),
    }
    return JsonResponse(data, status=200)

# DELETE /countries/<name>/
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_country(request, name):
    country = Country.objects.filter(name__iexact=name).first()
    if not country:
        return JsonResponse({"error": "Country not found"}, status=404)
    country.delete()
    return HttpResponse(status=204)

# GET /status/
@require_http_methods(["GET"])
def top_level_status(request):
    total = Country.objects.count()
    latest = Country.objects.order_by("-last_refreshed_at").first()
    last_refreshed_at = _iso(latest.last_refreshed_at) if latest and latest.last_refreshed_at else None
    return JsonResponse({"total_countries": total, "last_refreshed_at": last_refreshed_at}, status=200)

# GET /countries/image/
@require_http_methods(["GET"])
def countries_image(request):
    total = Country.objects.count()
    last = Country.objects.order_by("-last_refreshed_at").first()
    last_text = _iso(last.last_refreshed_at) if last and last.last_refreshed_at else "N/A"

    img = Image.new("RGB", (800, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((20, 40), f"Total countries: {total}", fill=(0, 0, 0), font=font)
    draw.text((20, 80), f"Last refreshed: {last_text}", fill=(0, 0, 0), font=font)
    draw.text((20, 120), f"Generated: {datetime.now(timezone.utc).isoformat()}", fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png", status=200)
