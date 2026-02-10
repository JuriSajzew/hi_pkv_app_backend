# This script imports insurance data from a JSON file into the database.
# It assumes that the JSON file is located in the same project directory
# and is named 'insurance_data.json'.

import json
from users.models import InsuranceCompany, Tariff

# Load the JSON file containing the insurance data
with open('pkv_backend/insurance_data.json', encoding='utf-8') as f:
    data = json.load(f)

# Iterate over all insurance companies in the JSON data
for company_data in data:
    # Create the insurance company if it does not exist,
    # or retrieve it if it already exists
    company, _ = InsuranceCompany.objects.get_or_create(
        name=company_data["name"]
    )
    print(f"Company: {company.name}")

    # Cache for additional tariffs so they are created only once
    additional_tariff_map = {}

    # Step 1: Create all additional tariffs for this company
    for tariff_data in company_data.get("tariffs", []):
        for add_data in tariff_data.get("additional_tariffs", []):
            add_name = add_data["name"]

            # Create or retrieve the additional tariff
            add_tariff, _ = Tariff.objects.get_or_create(
                name=add_name,
                company=company,
                type="additional"
            )

            # Store it in the cache for later linking
            additional_tariff_map[add_name] = add_tariff

    # Step 2: Create main tariffs and link them to their additional tariffs
    for tariff_data in company_data.get("tariffs", []):
        main_name = tariff_data["name"]

        # Create or retrieve the main tariff
        main_tariff, _ = Tariff.objects.get_or_create(
            name=main_name,
            company=company,
            type="main"
        )

        # Link additional tariffs (ManyToMany relationship)
        additional_tariffs = [
            additional_tariff_map[add["name"]]
            for add in tariff_data.get("additional_tariffs", [])
            if add["name"] in additional_tariff_map
        ]

        # Set the additional tariffs for the main tariff
        main_tariff.additional_tariffs.set(additional_tariffs)
        main_tariff.save()

        print(f"Main Tariff: {main_tariff.name}")
        if additional_tariffs:
            print(f"  Additional: {[t.name for t in additional_tariffs]}")

# Import finished successfully
print("✅ Import completed.")
# End of file
