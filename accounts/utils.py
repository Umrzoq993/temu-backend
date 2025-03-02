import openpyxl
import datetime
import decimal
from rapidfuzz import fuzz
from .models import City, Region, Product
from .sms import transmit_sms


def get_or_create_normalized_city(city_name, region_obj=None, threshold=80):
    """
    Uses fuzzy matching to find a City instance that closely matches the provided city_name.
    If a match with a similarity score >= threshold is found, returns that City.
    Otherwise, creates and returns a new City record.

    If region_obj is provided, limits the search to that region and uses it when creating a new City.
    """
    normalized_input = city_name.strip().lower()

    if region_obj:
        cities = City.objects.filter(region=region_obj)
    else:
        cities = City.objects.all()

    best_match = None
    highest_score = 0

    for city in cities:
        score = fuzz.token_sort_ratio(normalized_input, city.name.lower())
        if score > highest_score:
            highest_score = score
            best_match = city

    if highest_score >= threshold:
        return best_match
    else:
        if region_obj is None:
            raise ValueError("Region object must be provided to create a new City.")
        return City.objects.create(name=city_name.strip(), region=region_obj)


def format_text(text):
    """
    Formats the text based on the following rules:
    - If the text has exactly three words:
        * The first and second words: capitalize the first letter and lowercase the rest.
        * The third word: all lowercased.
    - Otherwise:
        * The first word: capitalize the first letter and lowercase the rest.
        * All other words: lowercased.
    """
    words = text.split()
    if not words:
        return ""

    def format_word_cap(word):
        parts = word.split("'")
        formatted_parts = [parts[0].capitalize()] + [p.lower() for p in parts[1:]]
        return "'".join(formatted_parts)

    def format_word_lower(word):
        parts = word.split("'")
        return "'".join([p.lower() for p in parts])

    formatted_words = []
    if len(words) == 3:
        formatted_words.append(format_word_cap(words[0]))
        formatted_words.append(format_word_cap(words[1]))
        formatted_words.append(format_word_lower(words[2]))
    else:
        formatted_words.append(format_word_cap(words[0]))
        for word in words[1:]:
            formatted_words.append(format_word_lower(word))
    return " ".join(formatted_words)


def import_products_from_excel(excel_file):
    """
    Import products from an Excel file using openpyxl.
    Assumes data starts from row 2 with the following fixed column indices:
      0: Serial number (ignored)
      1: Order status ("确认订单" => confirmed, else pending)
      2: Date (e.g., "2025-01-06 23:59:34")
      3: Order number
      4: Weight (string with comma as decimal separator or a float)
      5: English product name
      6: Chinese product name (ignored)
      7: Address
      8: City (if contains '/', use part after the slash then format it)
      9: Region (if contains '/', use part after the slash then format it)
     10: Phone number

    Returns a list of messages describing the result.
    """
    wb = openpyxl.load_workbook(excel_file)
    ws = wb.active
    messages = []
    imported_count = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        try:
            date_str = row[2]
            order_number = row[3]
            weight_raw = row[4]
            address = row[7]
            city_field = row[8]
            region_field = row[9]
            phone = row[10]

            # Convert weight:
            if weight_raw is not None:
                if isinstance(weight_raw, str):
                    weight_str = weight_raw.replace(',', '.')
                else:
                    weight_str = str(weight_raw)
            else:
                weight_str = "0"
            weight = decimal.Decimal(weight_str)

            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                messages.append(f"Error parsing date {date_str} for order {order_number}: {e}")
                continue

            # Process city: if '/' is present, take the part after the slash; otherwise, use the full string.
            if city_field and isinstance(city_field, str):
                if '/' in city_field:
                    raw_city = city_field.split('/', 1)[1].strip()
                else:
                    raw_city = city_field.strip()
                city_name = format_text(raw_city)
            else:
                city_name = ""

            # Process region similarly:
            if region_field and isinstance(region_field, str):
                if '/' in region_field:
                    raw_region = region_field.split('/', 1)[1].strip()
                else:
                    raw_region = region_field.strip()
                region_name = format_text(raw_region)
            else:
                region_name = ""

            # Convert phone to string and ensure it starts with '+998'
            if phone is not None:
                phone = str(phone).strip()
                if not phone.startswith('+998'):
                    phone = '+998' + phone

            # Get or create Region:
            region_obj = None
            if region_name:
                region_obj, _ = Region.objects.get_or_create(name=region_name)
            # Get or create City using rapidfuzz-based normalization.
            city_obj = None
            if city_name and region_obj:
                city_obj = get_or_create_normalized_city(city_name, region_obj=region_obj)
            else:
                city_obj = None

            # Create or get the Product.
            product, created = Product.objects.get_or_create(
                order_number=order_number,
                defaults={
                    'date': date_obj,
                    'weight': weight,
                    'address': address,
                    'city': city_obj,
                    'region': region_obj,
                    'phone_number': phone,
                }
            )
            if created:
                imported_count += 1
            else:
                messages.append(f"Product {order_number} already exists.")
        except Exception as e:
            messages.append(f"Error processing row for order {order_number}: {e}")
            continue

    messages.append(f"Imported {imported_count} products successfully.")
    return messages
