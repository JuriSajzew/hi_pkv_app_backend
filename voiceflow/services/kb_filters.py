"""
Voiceflow variable builder.
Constructs variables to send to Voiceflow Agent.
"""
from .mappings import get_company_code, get_tariff_group, get_additional_tariff_group


def _get_key(obj) -> str:
    """Extract unique identifier from model instance (code > slug > name)."""
    if not obj:
        return ""
    return (getattr(obj, "code", None) or getattr(obj, "slug", None) or getattr(obj, "name", "")).strip()


def _get_additional_groups(manager) -> list[str]:
    """Extract all addon tariff groups from a Django related manager."""
    if not manager:
        return []
    return [get_additional_tariff_group(_get_key(t)) for t in manager.all() if _get_key(t)]


def build_variables(profile) -> dict:
    """
    Build Voiceflow session variables from user profile.
    
    Sends main_tariff and additional_tariffs as separate variables
    so the Voiceflow Agent can filter the KB precisely.
    """
    company = get_company_code(_get_key(getattr(profile, "insurance_company", None)))
    tariff = get_tariff_group(_get_key(getattr(profile, "tariff", None)))
    addons = _get_additional_groups(getattr(profile, "additional_tariffs", None))
    
    return {
        "insurance_company": company,
        "main_tariff": tariff,
        "additional_tariffs": ", ".join(addons) if addons else "",
    }