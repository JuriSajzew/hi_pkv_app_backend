"""
Mapping configuration for Voiceflow KB metadata.
Maps Django model values to Voiceflow metadata keys.
"""
import json
from pathlib import Path

# Load mapping data from JSON file
_data_path = Path(__file__).parent / "mapping_data.json"
_data = json.loads(_data_path.read_text(encoding="utf-8"))

COMPANY_CODES = _data["company_codes"]
TARIFF_GROUPS = _data["tariff_groups"]
ADDITIONAL_TARIFF_GROUPS = _data["additional_tariff_groups"]


def get_company_code(name: str) -> str:
    """Map company name to Voiceflow metadata key."""
    return COMPANY_CODES.get(name, name)


def get_tariff_group(name: str) -> str:
    """Map tariff name to Voiceflow metadata group."""
    return TARIFF_GROUPS.get(name, name)


def get_additional_tariff_group(name: str) -> str:
    """Map additional tariff name to Voiceflow metadata key."""
    return ADDITIONAL_TARIFF_GROUPS.get(name, name)