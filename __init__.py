# -*- coding: utf-8 -*-

from calibre.customize import InterfaceActionBase
from calibre.gui2 import error_dialog, info_dialog

# ---- 変換テーブル ----
# 全角数字 → 半角数字
ZEN2HAN = str.maketrans(
    "０１２３４５６７８９　",
    "0123456789 "
)

def normalize_text(s: str) -> str:
    if not s:
        return s
    return s.translate(ZEN2HAN)

# ---- UI プラグイン本体 ----
class NormalizeTitleSeries(InterfaceAction):

    name = 'Normalize Title / Series'
    description = '全角数字・スペースを半角に正規化'
    author = 'Akito Yoshitake'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    def genesis(self):
        # メニュー追加
        self.qaction.setText('Normalize Title / Series')
        self.qaction.triggered.connect(self.run)

    def run(self):
        db = self.gui.current_db
        view = self.gui.library_view

        # 選択されている book_id を取得
        book_ids = view.get_selected_ids()

        if not book_ids:
            error_dialog(
                self.gui,
                'No selection',
                '本が選択されていません',
                show=True
            )
            return

        changed = 0

        for book_id in book_ids:
            mi = db.get_metadata(book_id, index_is_id=True)

            new_title = normalize_text(mi.title)
            new_series = normalize_text(mi.series)

            if new_title != mi.title:
                mi.title = new_title
                changed += 1

            if new_series != mi.series:
                mi.series = new_series
                changed += 1

            db.set_metadata(book_id, mi, set_title=True, set_series=True)

        info_dialog(
            self.gui,
            'Done',
            f'{len(book_ids)}冊処理しました\n変更フィールド数: {changed}',
            show=True
        )
