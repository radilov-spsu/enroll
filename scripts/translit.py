#!/usr/bin/env python3
"""
Читает students/<login>.yml, валидирует и печатает пары key=value
для GITHUB_OUTPUT: slug, repo_name, fio, group, year.

Использование:
    python scripts/translit.py students/ivan-petrov.yml
"""
import os
import re
import sys
from datetime import datetime, timezone

import yaml

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

NAME_RE = re.compile(r"^[А-Яа-яЁёA-Za-zІіЇїЄєҐґЎў][А-Яа-яЁёA-Za-zІіЇїЄєҐґЎў\-' ]{0,48}$")
GROUP_RE = re.compile(r"^[A-Za-zА-Яа-яЁё0-9\-_. /]{1,32}$")


def translit(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch in MAP:
            out.append(MAP[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        else:
            out.append('-')
    slug = ''.join(out)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def academic_year() -> str:
    """Учебный год: с августа считается уже следующий."""
    env = os.environ.get('COURSE_YEAR', '').strip()
    if env:
        if not re.fullmatch(r'[0-9]{4}(-[0-9]{2,4})?', env):
            fail(f"COURSE_YEAR имеет недопустимый формат: {env!r}")
        return env
    now = datetime.now(timezone.utc)
    return str(now.year if now.month >= 8 else now.year - 1)


def fail(msg: str) -> None:
    print(f"::error::{msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("Ожидается ровно один аргумент: путь к yml-файлу студента")
    path = sys.argv[1]

    try:
        with open(path, encoding='utf-8') as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        fail(f"Файл {path} не найден")
    except yaml.YAMLError as exc:
        fail(f"Файл {path} — некорректный YAML: {exc}")

    if not isinstance(data, dict):
        fail(f"Файл {path} должен содержать словарь ключ: значение")

    unknown = set(data) - {'last_name', 'first_name', 'middle_name', 'group'}
    if unknown:
        fail(f"Лишние поля в {path}: {', '.join(sorted(unknown))}")

    parts = []
    for key in ('last_name', 'first_name', 'middle_name'):
        value = data.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            if key == 'middle_name':
                continue  # отчество необязательно
            fail(f"В {path} не заполнено обязательное поле {key}")
        if not isinstance(value, str):
            fail(f"Поле {key} в {path} должно быть строкой")
        value = value.strip()
        if not NAME_RE.fullmatch(value):
            fail(f"Поле {key} в {path} содержит недопустимые символы: {value!r}")
        parts.append(value)

    group = data.get('group')
    if not isinstance(group, str) or not group.strip():
        fail(f"В {path} не заполнено обязательное поле group")
    group = group.strip()
    if not GROUP_RE.fullmatch(group):
        fail(f"Поле group в {path} содержит недопустимые символы: {group!r}")

    fio = ' '.join(parts)
    slug = '-'.join(translit(p) for p in parts if translit(p))
    if not slug:
        fail(f"Не удалось построить имя репозитория из ФИО {fio!r}")

    year = academic_year()
    repo_name = f"{slug}-{year}"
    # GitHub: имя репозитория до 100 символов
    if len(repo_name) > 100:
        repo_name = f"{slug[:100 - len(year) - 1]}-{year}"

    print(f"slug={slug}")
    print(f"repo_name={repo_name}")
    print(f"fio={fio}")
    print(f"group={group}")
    print(f"year={year}")


if __name__ == '__main__':
    main()
