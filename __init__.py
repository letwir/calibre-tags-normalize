from calibre.customize import InterfaceActionBase
from calibre.gui2 import info_dialog
import unicodedata

class NormalizeTitleSeries(InterfaceActionBase):
    name = 'Normalize Title / Series'

    def genesis(self):
        self.qaction.setText(self.name)
        self.qaction.triggered.connect(self.run)

    def run(self):
        db = self.gui.current_db.new_api
        view = self.gui.library_view

        rows = view.selectionModel().selectedRows()
        if not rows:
            info_dialog(self.gui, 'Normalize', 'No books selected', show=True)
            return

        def norm(s):
            if not s:
                return s
            return unicodedata.normalize('NFKC', s).replace('\u3000', ' ')

        book_ids = [view.model().id(row) for row in rows]

        with db.transaction():
            for book_id in book_ids:
                mi = db.get_metadata(book_id)
                mi.title = norm(mi.title)
                mi.series = norm(mi.series)
                db.set_metadata(
                    book_id,
                    mi,
                    set_title=True,
                    set_series=True
                )

        # ★ これが無いと画面が更新されない
        view.model().refresh_ids(book_ids)

        info_dialog(
            self.gui,
            'Normalize',
            f'Updated {len(book_ids)} book(s)',
            show=True
        )
