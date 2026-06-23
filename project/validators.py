import re


def validate_egn(egn):
    if not egn or not re.match(r'^\d{10}$', str(egn)):
        return False
    weights = [2, 4, 8, 5, 10, 9, 7, 3, 6]
    checksum = sum(int(egn[i]) * weights[i] for i in range(9)) % 11
    if checksum == 10:
        checksum = 0
    return checksum == int(egn[9])


def validate_eik(eik):
    if not eik or not re.match(r'^\d{9,13}$', str(eik)):
        return False
    return True


def validate_identifier(identifier):
    if not identifier:
        return False, 'Идентификаторът е задължителен.'
    identifier = str(identifier)
    if re.match(r'^\d{10}$', identifier):
        if validate_egn(identifier):
            return True, ''
        return False, 'Невалидно ЕГН - грешна контролна цифра.'
    if re.match(r'^\d{9,13}$', identifier):
        if validate_eik(identifier):
            return True, ''
        return False, 'Невалидно ЕИК.'
    return False, 'Идентификаторът трябва да е 10-цифрено ЕГН или 9-13 цифрено ЕИК.'


def validate_phone(phone):
    if not phone:
        return True, ''
    phone = phone.strip()
    if re.match(r'^(\+?\d{7,15})$', phone):
        return True, ''
    return False, 'Невалиден телефонен номер. Допустими са само цифри и + (7-15 символа).'


def validate_cfr(cfr):
    if not cfr:
        return False, 'CFR номерът е задължителен.'
    if re.match(r'^[A-Z]{3}\d{7,9}$', cfr.strip()):
        return True, ''
    return False, 'CFR номерът трябва да е формат: 3 главни букви + 7-9 цифри (напр. BGR000001234).'


def validate_password_strength(password):
    if len(password) < 6:
        return False, 'Паролата трябва да е поне 6 символа.'
    return True, ''
