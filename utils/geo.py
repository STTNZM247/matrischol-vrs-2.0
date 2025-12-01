try:
    import requests
except Exception:
    requests = None


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _user_agent():
    # Cumplir política de Nominatim: proveer User-Agent identificable
    return "matrischol/1.0 (admin@matrischol.local)"


def validate_and_normalize_address(address: str, country: str = "CO", timeout: float = 4.0):
    """Valida una dirección usando Nominatim (OSM) y devuelve datos normalizados.

    Retorna dict:
    { ok: bool, normalized: str|None, lat: float|None, lon: float|None, raw: dict|None }

    Nota: Este método consulta un servicio externo con límites de uso.
    Úsalo con moderación y preferiblemente junto a autocompletado en el frontend.
    """
    if not address or not address.strip():
        return {"ok": False, "normalized": None, "lat": None, "lon": None, "raw": None}
    # Si la dependencia no está disponible, hacer fallback suave para no bloquear el servidor/formulario
    if requests is None:
        return {"ok": True, "normalized": address.strip(), "lat": None, "lon": None, "raw": {"warning": "requests_missing"}}
    params = {
        "q": address,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
        "countrycodes": (country or "").lower(),
    }
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": _user_agent()}, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        if not data:
            return {"ok": False, "normalized": None, "lat": None, "lon": None, "raw": None}
        hit = data[0]
        # Heurística simple de calidad: existencia de lat/lon y importance >= 0.2
        lat = float(hit.get("lat")) if hit.get("lat") else None
        lon = float(hit.get("lon")) if hit.get("lon") else None
        importance = float(hit.get("importance", 0) or 0)
        display = hit.get("display_name")
        ok = bool(lat is not None and lon is not None and importance >= 0.2)
        return {"ok": ok, "normalized": display, "lat": lat, "lon": lon, "raw": hit}
    except Exception:
        # Ante fallo de red o límites, no bloquear por defecto
        return {"ok": False, "normalized": None, "lat": None, "lon": None, "raw": None}
