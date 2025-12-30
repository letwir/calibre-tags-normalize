#!python3
# やること。
# * {title},{series}の全角数字、スペースを半角にする
# * 
# TODO
# * 以上をGUIでポチポチON/OFFできるようにする
# * 書籍データを各EPUB、CBZに反映できるようにする
__name__        = 'Normalize Title/Series'
__version__     = (0, 0, 1)
__license__   = 'CC0'
__copyright__ = '2025, letwir'

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import info_dialog
import unicodedata

def normalize(s):
    if not s:
        return s
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('\u3000', ' ')
    return s

class NormalizeTitleSeries(InterfaceAction):

    name = 'Normalize Title/Series'
    action_spec = (
        'Normalize Title/Series',
        None,
        'Convert full-width digits/spaces to half-width in title and series',
        None
    )

    def genesis(self):
        self.qaction.triggered.connect(self.run)

    def run(self):
        db = self.gui.current_db
        view = self.gui.library_view

        rows = view.selectionModel().selectedRows()
        if not rows:
            info_dialog(self.gui, 'Normalize',
                        'No books selected', show=True)
            return

        book_ids = [view.model().id(row) for row in rows]

        changed = 0

        for book_id in book_ids:
            mi = db.get_metadata(book_id, index_is_id=True)

            new_title = normalize(mi.title)
            new_series = normalize(mi.series)

            if new_title != mi.title or new_series != mi.series:
                mi.title = new_title
                mi.series = new_series
                db.set_metadata(book_id, mi)
                changed += 1

        info_dialog(
            self.gui,
            'Normalize',
            f'Updated {changed} book(s)',
            show=True
        )