def analyse_image(image_path):

    result = {
        "text": "",
        "width": None,
        "height": None,
        "sharpness": None,
        "quality_note": "Image analysis could not be completed."
    }

    # BASIC IMAGE ANALYSIS
    try:
        from PIL import Image, ImageStat, ImageFilter

        image = Image.open(image_path).convert("RGB")

        result["width"], result["height"] = image.size

        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)

        sharpness = ImageStat.Stat(edges).var[0]

        result["sharpness"] = round(sharpness, 2)

        if sharpness >= 25 and min(image.size) >= 250:
            result["quality_note"] = (
                "Image appears suitable for a basic visual check."
            )
        else:
            result["quality_note"] = (
                "Image may be blurry or low-resolution. "
                "Upload a clearer image if possible."
            )

    except Exception as error:
        result["quality_note"] = (
            "Image could not be read: " + str(error)
        )

    # OCR TEXT EXTRACTION
    try:
        import pytesseract
        from PIL import Image

        text = pytesseract.image_to_string(
            Image.open(image_path)
        )

        result["text"] = text.strip()

    except Exception:
        result["text"] = ""
        result["ocr_note"] = (
            "OCR is unavailable. Install Tesseract OCR "
            "to extract label text."
        )

    return result
