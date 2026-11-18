# PRODUCT-SPECIFIC SAMPLE COMPLIANCE CHECKER


PRODUCT_RULES = {

    "Fresh Mangoes": [

        {
            "name": "Mango variety",
            "keywords": ["variety", "mango variety"]
        },

        {
            "name": "Grade or quality class",
            "keywords": ["grade", "class"]
        },

        {
            "name": "Size or count information",
            "keywords": ["size", "count"]
        },

        {
            "name": "Country of origin",
            "keywords": [
                "country of origin",
                "product of",
                "made in"
            ]
        },

        {
            "name": "Batch or lot number",
            "keywords": ["batch", "lot"]
        },

        {
            "name": "Packing or harvest date",
            "keywords": [
                "packing date",
                "packed on",
                "harvest date"
            ]
        }
    ],


    "Cotton T-Shirts": [

        {
            "name": "Fabric composition",
            "keywords": [
                "100% cotton",
                "cotton",
                "cotton blend"
            ]
        },

        {
            "name": "T-shirt size",
            "keywords": [
                "size",
                "small",
                "medium",
                "large",
                "xl"
            ]
        },

        {
            "name": "Washing or care instructions",
            "keywords": [
                "wash",
                "machine wash",
                "care instructions",
                "hand wash"
            ]
        },

        {
            "name": "Country of origin",
            "keywords": [
                "country of origin",
                "made in",
                "product of"
            ]
        },

        {
            "name": "Manufacturer or brand",
            "keywords": [
                "manufacturer",
                "brand",
                "manufactured by"
            ]
        }
    ],


    "Bluetooth Speaker": [

        {
            "name": "Brand or model information",
            "keywords": [
                "brand",
                "model",
                "model no"
            ]
        },

        {
            "name": "Electrical input rating",
            "keywords": [
                "input",
                "voltage",
                "rated power",
                "watt"
            ]
        },

        {
            "name": "Battery information",
            "keywords": [
                "battery",
                "mah",
                "lithium"
            ]
        },

        {
            "name": "Country of origin",
            "keywords": [
                "made in",
                "country of origin",
                "product of"
            ]
        },

        {
            "name": "Safety or conformity marking reference",
            "keywords": [
                "ce marking",
                "fcc",
                "bis"
            ]
        }
    ],


    "Turmeric Powder": [

        {
            "name": "Product ingredients",
            "keywords": [
                "ingredients",
                "turmeric",
                "100% turmeric"
            ]
        },

        {
            "name": "Net weight information",
            "keywords": [
                "net weight",
                "net wt",
                "weight"
            ]
        },

        {
            "name": "Batch or lot number",
            "keywords": [
                "batch",
                "lot"
            ]
        },

        {
            "name": "Manufacturing or packing date",
            "keywords": [
                "manufacturing date",
                "packed on",
                "packing date",
                "mfg"
            ]
        },

        {
            "name": "Expiry or best-before information",
            "keywords": [
                "expiry",
                "expires",
                "best before",
                "use before"
            ]
        },

        {
            "name": "Country of origin",
            "keywords": [
                "made in",
                "country of origin",
                "product of"
            ]
        }
    ]

}


def assess_compliance(
    product_name,
    category,
    destination,
    batch_number,
    net_weight,
    country_origin,
    extracted_text,
    image_results
):

    score = 100

    checks = []
    observations = []

    # STEP 1: GENERAL PRODUCT INFORMATION

    fields = [
        ("Product name", product_name),
        ("Product type", category),
        ("Export destination", destination),
        ("Batch / lot number", batch_number),
        ("Net weight / quantity", net_weight),
        ("Country of origin", country_origin)
    ]

    for label, value in fields:

        passed = bool(value and value.strip())

        checks.append({
            "name": label,
            "result": (
                "Information provided"
                if passed else "Information missing"
            ),
            "passed": passed
        })

        if not passed:

            observations.append(
                label + " has not been provided."
            )

            score -= 5


    # STEP 2: CHECK WHETHER PRODUCT TYPE IS SUPPORTED

    if category not in PRODUCT_RULES:

        observations.append(
            "No product-specific demonstration rules "
            "are configured for this product."
        )

        score -= 20

    else:

        # STEP 3: CHECK PRODUCT-SPECIFIC LABEL INFORMATION

        text = (extracted_text or "").lower()

        for rule in PRODUCT_RULES[category]:

            found = any(
                keyword in text
                for keyword in rule["keywords"]
            )

            checks.append({

                "name": rule["name"],

                "result": (
                    "Possible information detected by OCR"
                    if found
                    else "Not detected in extracted text"
                ),

                "passed": found

            })

            if not found:

                observations.append(
                    rule["name"]
                    + " was not detected in the uploaded label."
                )

                score -= 5


    # STEP 4: CHECK IMAGE QUALITY

    for index, image in enumerate(image_results, start=1):

        quality_note = image.get(
            "quality_note",
            "Image quality could not be checked."
        )

        passed = "suitable" in quality_note.lower()

        checks.append({

            "name": "Image " + str(index) + " quality",

            "result": quality_note,

            "passed": passed

        })

        if not passed:

            observations.append(
                "Image " + str(index)
                + " may need a clearer photograph."
            )

            score -= 5


    # STEP 5: CALCULATE FINAL SCORE

    score = max(0, min(100, score))


    # STEP 6: GENERATE ASSESSMENT STATUS

    if score >= 80 and all(
        item["passed"] for item in checks
    ):

        status = "Compliant (preliminary)"
        status_class = "good"

    elif score >= 55:

        status = "Requires review"
        status_class = "review"

    else:

        status = "Potentially non-compliant"
        status_class = "bad"


    # STEP 7: ADD IMPORTANT DISCLAIMER

    if not observations:

        observations.append(
            "No issue was identified by the configured "
            "demonstration checks."
        )

    observations.append(
        "OCR results only indicate possible text matches. "
        "They do not verify the accuracy or legal validity "
        "of product information."
    )

    observations.append(
        "The assessment uses sample rules and is not "
        "official export certification."
    )


    return {

        "score": score,

        "status": status,

        "status_class": status_class,

        "checks": checks,

        "observations": observations,

        "review_required": (
            status != "Compliant (preliminary)"
        )

    }