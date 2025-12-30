# -*- coding: utf-8 -*-
"""
Normalization helpers used by the plugin wrapper.

Normalize fullwidth digits (０-９) and fullwidth space (U+3000)
to ASCII equivalents, applied to title and series fields
for selected books in the calibre GUI.
"""

# ---- fullwidth → halfwidth map ----
FW_MAP = {0x3000: 0x20}
for i in range(10):
    FW_MAP[0xFF10 + i] = ord('0') + i


def normalize_text(s):
    if not s:
        return s
    return s.translate(FW_MAP)


def normalize_selection_via_gui(gui):
    """
    Mutate calibre DB for selected books.
    """
    db = gui.current_db
    view = gui.library_view
    book_ids = view.get_selected_ids()

    if not book_ids:
        return {
            'processed': 0,
            'changed': 0,
            'note': 'no selection'
        }

    changed = 0

    for book_id in book_ids:
        mi = db.get_metadata(book_id, index_is_id=True)

        new_title = normalize_text(mi.title)
        new_series = normalize_text(mi.series)

        updated = False

        if new_title != mi.title:
            mi.title = new_title
            updated = True

        if new_series != mi.series:
            mi.series = new_series
            updated = True

        if updated:
            db.set_metadata(
                book_id,
                mi,
                set_title=True,
                set_series=True
            )
            changed += 1

    return {
        'processed': len(book_ids),
        'changed': changed
    }
