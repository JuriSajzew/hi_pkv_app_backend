# Dieses Skript importiert Versicherungsdaten aus einer JSON-Datei in die Datenbank.
# Es wird davon ausgegangen, dass die JSON-Datei im gleichen Verzeichnis liegt und den
# Namen 'insurance_data.json' trägt.
import json
from users.models import InsuranceCompany, Tariff

# JSON-Datei laden
with open('pkv_backend/insurance_data.json', encoding='utf-8') as f:
    data = json.load(f)

for company_data in data:
    # Versicherung anlegen oder holen
    company, _ = InsuranceCompany.objects.get_or_create(name=company_data["name"])
    print(f"Company: {company.name}")

    # Zusatztarife-Cache (damit sie nur einmal angelegt werden)
    additional_tariff_map = {}

    # Schritt 1: Alle Zusatztarife für diese Firma einmal anlegen
    for tariff_data in company_data.get("tariffs", []):
        for add_data in tariff_data.get("additional_tariffs", []):
            add_name = add_data["name"]
            add_tariff, _ = Tariff.objects.get_or_create(
                name=add_name,
                company=company,
                type="additional"
            )
            additional_tariff_map[add_name] = add_tariff

    # Schritt 2: Haupttarife anlegen und verknüpfen
    for tariff_data in company_data.get("tariffs", []):
        main_name = tariff_data["name"]
        main_tariff, _ = Tariff.objects.get_or_create(
            name=main_name,
            company=company,
            type="main"
        )

        # Zusatz-Tarife verknüpfen (ManyToMany)
        additional_tariffs = [
            additional_tariff_map[add["name"]]
            for add in tariff_data.get("additional_tariffs", [])
            if add["name"] in additional_tariff_map
        ]
        main_tariff.additional_tariffs.set(additional_tariffs)
        main_tariff.save()

        print(f"Main Tariff: {main_tariff.name}")
        if additional_tariffs:
            print(f"  Zusatz: {[t.name for t in additional_tariffs]}")

print("✅ Import abgeschlossen.")
# Ende der Datei