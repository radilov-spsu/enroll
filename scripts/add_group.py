#!/usr/bin/env python3
"""
Добавляет группу нового набора в выпадающий список формы заявки.

    python3 scripts/add_group.py            # группа текущего года
    python3 scripts/add_group.py --year 2027
    python3 scripts/add_group.py --dry-run

Правит файл текстом, а не через yaml.dump: иначе потеряются комментарии
и порядок ключей в шаблоне формы.
"""
import argparse
import re
import sys
from datetime import datetime, timezone

FORM = '.github/ISSUE_TEMPLATE/enrollment.yml'
PATTERN = 'ФТ{yy}ДР62ПФ'


def trim(groups: list, keep: int):
    """Оставляет keep самых свежих наборов. Год берём из двух цифр в имени;
    имена без цифр не трогаем — они могли быть добавлены вручную."""
    def year_of(name: str) -> int:
        m = re.search(r'(\d{2})', name)
        return int(m.group(1)) if m else -1

    numbered = [g for g in groups if year_of(g) >= 0]
    manual = [g for g in groups if year_of(g) < 0]

    ordered = sorted(set(numbered), key=year_of, reverse=True)
    kept, dropped = ordered[:keep], ordered[keep:]
    return kept + manual, dropped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, help='год набора, по умолчанию текущий')
    ap.add_argument('--pattern', default=PATTERN,
                    help='шаблон имени группы, {yy} — две цифры года')
    ap.add_argument('--form', default=FORM)
    ap.add_argument('--keep', type=int, default=5,
                    help='сколько наборов держать в списке (бакалавриат — 4 года, '
                         'плюс один на переходный период)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    year = args.year or datetime.now(timezone.utc).year
    group = args.pattern.format(yy=f'{year % 100:02d}')

    text = open(args.form, encoding='utf-8').read()

    # находим поле group, затем первый список options под ним
    anchor = re.search(r'^\s+id:\s*group\s*$', text, re.M)
    if not anchor:
        sys.exit(f'Не нашёл поле group в {args.form}')
    opts = re.search(r'^\s+options:\s*\n((?:\s+-\s+.+\n)+)', text[anchor.end():], re.M)
    if not opts:
        sys.exit(f'У поля group нет списка options в {args.form}')

    # смещения внутри полного текста
    start = anchor.end() + opts.start(1)
    end = anchor.end() + opts.end(1)
    options_block = opts.group(1)
    existing = re.findall(r'-\s*(\S+)', options_block)

    first_line = options_block.split('\n')[0]
    indent = first_line[:len(first_line) - len(first_line.lstrip())]

    groups = existing if group in existing else [group] + existing
    kept, dropped = trim(groups, args.keep)

    if group in existing and not dropped:
        print(f'Группа {group} уже есть в списке — ничего не делаю.')
        print('changed=false')
        return

    new_block = ''.join(f'{indent}- {g}\n' for g in kept)
    text = text[:start] + new_block + text[end:]

    if group not in existing:
        print(f'Добавляю группу {group}. Было: {", ".join(existing)}')
    if dropped:
        print(f'Убираю выпустившиеся: {", ".join(dropped)}')
    if args.dry_run:
        print('(--dry-run: файл не изменён)')
        print('changed=false')
        return

    open(args.form, 'w', encoding='utf-8').write(text)
    print('changed=true')
    print(f'group={group}')
    print(f'year={year}')
    print(f'dropped={",".join(dropped)}')


if __name__ == '__main__':
    main()
