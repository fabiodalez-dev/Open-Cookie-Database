import pandas as pd
import sys
import unicodedata
import uuid


def validate_uuid(uuid_string):
    try:
        uuid.UUID(uuid_string)
    except ValueError:
        return False
    return True


def normalize_cookie_name(name):
    """Normalize names exactly as case-insensitive database consumers do."""
    normalized = unicodedata.normalize('NFKC', str(name).strip())
    normalized = ''.join(
        character
        for character in normalized
        if unicodedata.category(character) not in {'Cf', 'Zl', 'Zp'}
    )
    return normalized.casefold()


def validate_csv(file_path):
    df = pd.read_csv(file_path, sep=',', skipinitialspace=True)
    columns = ['ID', 'Platform', 'Category', 'Cookie / Data Key name', 'Domain', 'Description', 'Retention period', 'Data Controller', 'User Privacy & GDPR Rights Portals', 'Wildcard match']
    # The historical dataset also uses Necessary and Uncategorized. Keep the
    # validator aligned with the categories already accepted by the database.
    valid_categories = [
        'Functional',
        'Necessary',
        'Personalization',
        'Analytics',
        'Marketing',
        'Security',
        'Uncategorized',
    ]
    
    # Check if CSV has valid structure and contains necessary columns
    if not set(columns).issubset(df.columns):
        print("::error file=open-cookie-database.csv,line=1,col=1::CSV structure is not valid.")
        return False

    # Check if 'Category' column contains only valid values
    if not df['Category'].isin(valid_categories).all():
        print("::error file=open-cookie-database.csv,line=1,col=1::'Category' column must contain only these values: " + ', '.join(valid_categories))
        invalid_categories = df[~df['Category'].isin(valid_categories)]['Category']
        print("Invalid categories are:")
        print(invalid_categories)
        return False

    # Check if 'ID' column contains unique UUID values
    if not (df['ID'].apply(validate_uuid).all() and df['ID'].is_unique):
        print("::error file=open-cookie-database.csv,line=1,col=1::'ID' column must contain unique UUID values.")
        
        non_unique_ids = df[df.duplicated('ID', keep=False)][['ID', 'Cookie / Data Key name']]
        print("Non-unique IDs and corresponding cookie names are:")
        print(non_unique_ids)
        return False

    # Cookie lookups are case-insensitive. Normalize Unicode formatting
    # characters as well so visually identical names cannot bypass this check.
    normalized_names = df['Cookie / Data Key name'].apply(normalize_cookie_name)
    if not normalized_names.is_unique:
        duplicate_mask = normalized_names.duplicated(keep=False)
        non_unique_cookies = df.loc[duplicate_mask, 'Cookie / Data Key name']
        non_unique_cookies_str = ', '.join(non_unique_cookies)
        print(f"::error file=open-cookie-database.csv,line=1,col=1::'Cookie / Data Key name' contains normalized duplicates: {non_unique_cookies_str}.")
        return False

    print("CSV file is valid.")
    return True

if __name__ == '__main__':
    sys.exit(0 if validate_csv('open-cookie-database.csv') else 1)
