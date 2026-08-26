"""Транслитерация ФИО и сборка имени репозитория. Используется parse_issue.py."""
import os
import re
from datetime import datetime, timezone

# Практическая транслитерация (паспортного типа, но с привычными yu/ya/y).
MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    # украинские/белорусские буквы — на случай, если попадутся
    'і': 'i', 'ї': 'yi', 'є': 'ye', 'ґ': 'g', 'ў': 'u',
}


def translit(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch in MAP:
            out.append(MAP[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        else:
            out.append('-')
    return re.sub(r'-+', '-', ''.join(out)).strip('-')


def academic_year() -> str:
    """Учебный год: с августа считается уже следующий.

    Переопределяется переменной репозитория COURSE_YEAR.
    """
    env = os.environ.get('COURSE_YEAR', '').strip()
    if env:
        if not re.fullmatch(r'[0-9]{4}(-[0-9]{2,4})?', env):
            raise ValueError(f"COURSE_YEAR имеет недопустимый формат: {env!r}")
        return env
    now = datetime.now(timezone.utc)
    return str(now.year if now.month >= 8 else now.year - 1)


def repo_name(parts, year: str) -> str:
    """parts — [фамилия, имя, отчество]; отчество может отсутствовать."""
    slug = '-'.join(p for p in (translit(x) for x in parts) if p)
    if not slug:
        raise ValueError("Не удалось построить имя репозитория из ФИО")
    name = f"{slug}-{year}"
    if len(name) > 100:  # лимит GitHub на имя репозитория
        name = f"{slug[:100 - len(year) - 1]}-{year}"
    return name
