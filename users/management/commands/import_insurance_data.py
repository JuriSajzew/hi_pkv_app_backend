import json
from django.core.management.base import BaseCommand
from users.models import InsuranceCompany, Tariff

class Command(BaseCommand):
    help = "Importiert Versicherungsdaten aus JSON in die Datenbank"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Lösche vorher alle bestehenden Versicherungen und Tarife'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("🧹 Lösche alte Versicherungsdaten...")
            Tariff.objects.all().delete()
            InsuranceCompany.objects.all().delete()

        self.stdout.write("📥 Importiere neue Versicherungsdaten...")

        with open('pkv_backend/insurance_data.json', encoding='utf-8') as f:
            data = json.load(f)

        for company_data in data:
            company, _ = InsuranceCompany.objects.get_or_create(name=company_data["name"])
            self.stdout.write(f"🏢 {company.name}")

            # Cache für Zusatz-Tarife
            additional_tariff_map = {}

            # 1️⃣ Alle Zusatz-Tarife einmal anlegen
            for tariff_data in company_data.get("tariffs", []):
                for add_data in tariff_data.get("additional_tariffs", []):
                    add_name = add_data["name"]
                    add_tariff, _ = Tariff.objects.get_or_create(
                        name=add_name,
                        company=company,
                        type="additional"
                    )
                    additional_tariff_map[add_name] = add_tariff

            # 2️⃣ Haupttarife anlegen und Zusatz-Tarife verknüpfen
            for tariff_data in company_data.get("tariffs", []):
                main_tariff, _ = Tariff.objects.get_or_create(
                    name=tariff_data["name"],
                    company=company,
                    type="main"
                )

                additional_tariffs = [
                    additional_tariff_map[add["name"]]
                    for add in tariff_data.get("additional_tariffs", [])
                    if add["name"] in additional_tariff_map
                ]
                main_tariff.additional_tariffs.set(additional_tariffs)
                main_tariff.save()

                self.stdout.write(f"   ➕ {main_tariff.name}")
                if additional_tariffs:
                    self.stdout.write(f"      Zusatz: {[t.name for t in additional_tariffs]}")

        self.stdout.write("✅ Import abgeschlossen.")
