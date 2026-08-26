#!/usr/bin/env python3
"""
Разбирает тело заявки (GitHub Issue Form) и печатает пары key=value
для GITHUB_OUTPUT.

    python scripts/parse_issue.py body.md

Ошибки печатаются в stderr в виде готового текста для комментария студенту,
код возврата 1.
"""
import re
import sys

from translit import academic_year, repo_name

# Заголовок в теле issue -> внутреннее имя поля.
FIELDS = {
    'Фамилия': 'last_name',
    'Имя': 'first_name',
    'Группа': 'group',
}

NO_RESPONSE = '_No response_'

NAME_RE = re.compile(r"^[А-Яа-яЁёA-Za-zІіЇїЄєҐґЎў][А-Яа-яЁёA-Za-zІіЇїЄєҐґЎў\-' ]{0,48}$")
GROUP_RE = re.compile(r"^[A-Za-zА-Яа-яЁё0-9\-_. /]{1,32}$")

def parse_body(body: str) -> dict:
    """Тело issue-формы: '### Заголовок' + значение до следующего заголовка."""
    values = {}
    current = None
    buf = []
    for line in body.replace('\r\n', '\n').split('\n'):
        m = re.match(r'^###\s+(.+?)\s*$', line)
        if m:
            if current:
                values[current] = '\n'.join(buf).strip()
            current = FIELDS.get(m.group(1).strip())
            buf = []
        elif current:
            buf.append(line)
    if current:
        values[current] = '\n'.join(buf).strip()
    return values


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Ожидается один аргумент: путь к файлу с телом заявки")

    body = open(sys.argv[1], encoding='utf-8').read()
    values = parse_body(body)
    errors = []

    parts = []
    for key, label in (('last_name', 'Фамилия'), ('first_name', 'Имя')):
        value = values.get(key, '').strip()
        if value == NO_RESPONSE:
            value = ''
        if not value:
            errors.append(f"поле **{label}** не заполнено")
            continue
        if not NAME_RE.fullmatch(value):
            errors.append(
                f"поле **{label}** содержит недопустимые символы: `{value}` — "
                f"ожидаются только буквы, дефис и апостроф"
            )
            continue
        parts.append(value)

    group = values.get('group', '').strip()
    if group == NO_RESPONSE:
        group = ''
    if not group:
        errors.append("поле **Группа** не заполнено")
    elif not GROUP_RE.fullmatch(group):
        errors.append(f"поле **Группа** содержит недопустимые символы: `{group}`")

    if errors:
        print('\n'.join(f"- {e}" for e in errors), file=sys.stderr)
        sys.exit(1)

    year = academic_year()
    name = repo_name(parts, year)

    print(f"repo_name={name}")
    print(f"fio={' '.join(parts)}")
    print(f"group={group}")
    print(f"year={year}")


if __name__ == '__main__':
    main()
