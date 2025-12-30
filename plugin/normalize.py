# normalize.py

from typing import Optional
import unicodedata

def normalize_text(s: Optional[str]) -> Optional[str]:
    if not s:
        return s
    return unicodedata.normalize('NFKC', s)

# ----- メイン関数 -----
def normalize_selection_via_gui(gui):
    db = gui.current_db
    view = gui.library_view
    book_ids = view.get_selected_ids()

    if not book_ids:
        return

    for book_id in book_ids:
        mi = db.get_metadata(book_id, index_is_id=True)

        new_title = normalize_text(mi.title)
        new_series = normalize_text(mi.series)

        changed = False

        if new_title != mi.title:
            mi.title = new_title
            changed = True

        if new_series != mi.series:
            mi.series = new_series
            changed = True

        if changed:
            db.set_metadata(
                book_id,
                mi,
                set_title=True,
            )
