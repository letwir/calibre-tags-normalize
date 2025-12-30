#!python3
from typing import Optional
import unicodedata  # 正規化モジュール
import re           # 正規表現モジュール
from dataclasses import dataclass   # 実行結果を返すやつ
#-----
@dataclass(frozen=True)
class Result:
    '''実行結果データクラス'''
    processed: int
    changed: int
    source: str  # 'Normalize' / 'Amazon'

# ------------------------------------------- 文字一覧 -----
# 文字列変換 - 規則
RE_SYMBOLS = re.compile(r'([~∼〜]|\.{3})') # ユーザーご要望の変換対象記号(１文字用)
REMAP = {
    '~': '～',
    '∼': '～',
    '〜': '～',
    '...': '…',
}
RE_COLON_SPACE = re.compile(r'\s*(:|：)\s*') # コロン前後のスペース統一

VOLUME_RULES = [
    (
        re.compile(r'＞\s*(\d+)$'),
        r'＞ \1巻'
    ),    # ＞6 → ＞ 6巻
    (
        re.compile(r'\((\d+)巻*\)$'),
        r' \1巻'
    ),    # (6) →  6巻
    (
        re.compile(r':\s*(\d+)巻*$'),
        r' \1巻'
    ),    # : 6 →  6巻
]
#RE_ROMAN = re.compile(
#    r'(Vol\.?|Volume|Season|第|＞)'
#    r'(L?X{0,3})'
#    r'(IX|IV|V?I{0,3}))',
#    re.IGNORECASE
#)   # ローマ数字検出用正規表現(未実装)
ROMAN_MAP = {
    'I':  'Ⅰ',
    'II': 'Ⅱ',
    'III': 'Ⅲ',
    'IV': 'Ⅳ',
    'V':  'Ⅴ',
    'VI': 'Ⅵ',
    'VII': 'Ⅶ',
    'VIII': 'Ⅷ',
    'IX': 'Ⅸ',
    'X':  'Ⅹ',
    'XI': 'Ⅺ',
    'XII':'Ⅻ',
    'XIII':'ⅩⅢ','XIV':'ⅩⅣ','XV':'ⅩⅤ','XVI':'ⅩⅥ','XVII':'ⅩⅦ','XVIII':'ⅩⅧ','XIX':'ⅩⅨ','XX': 'ⅩⅩ',
    'XXI':'ⅩⅩⅠ','XXII':'ⅩⅩⅡ','XXIII':'ⅩⅩⅢ','XXIV':'ⅩⅩⅣ','XXV':'ⅩⅩⅤ','XXVI':'ⅩⅩⅥ','XXVII':'ⅩⅩⅦ','XXVIII':'ⅩⅩⅧ','XXIX':'ⅩⅩⅨ','XXX':'ⅩⅩⅩ',
}
RE_CTRL = re.compile(r'[\x00-\x1f]') # 制御文字範囲
RE_FORBIDDEN = str.maketrans({
    '\\': '＼',
    '/':  '／',
    ':':  '：',
    '*':  '＊',
    '?':  '？',
    '"':  '”',
    '<':  '＜',
    '>':  '＞',
    '|':  '｜',
})  # ファイル名禁止文字の全角変換
RE_WINDOWS_RESERVED_MAP = {
    'CON','PRN','AUX','NUL',
    *(f'COM{i}' for i in range(1,10)),
    *(f'LPT{i}' for i in range(1,10)),
}   # Windows予約語（大文字小文字無視）

# ------------------------------------------- 文字列操作関数 -----

# 文字列変換 - ロジック
def convert_text(s: Optional[str]) -> Optional[str]:
    if not s:
        return s
    # まず正規化
    s = unicodedata.normalize('NFKC', s)
    s = RE_CTRL.sub('', s)    # 制御文字削除
    s = s.translate(RE_FORBIDDEN)    # 禁止文字
    if s.upper() in RE_WINDOWS_RESERVED_MAP:
        s = f'_{s}'    # Windows予約名
    ## ユーザーの変換ルール
    s = RE_SYMBOLS.sub(lambda m: REMAP[m.group(0)], s) #１文字変換用
    s = RE_COLON_SPACE.sub(': ', s) # コロン前後のスペース統一
    for regex, repl in VOLUME_RULES:
        if regex.search(s):
            s = regex.sub(repl, s)   # 巻数ルール適用
    return s


# ------------------------------------------- メイン関数 -----
def normalize_main(gui) -> Result:
    # gui: calibre.gui2.main.CalibreMain
    ## guiには以下が含まれる
    # - gui.current_db: calibre.library.db.LiteDB
    # - gui.library_view: calibre.gui2.views.libraryview.LibraryView
    ## viewには以下が含まれる
    # - view.get_selected_ids(): 選択された本のIDリストを取得
    db = gui.current_db
    view = gui.library_view
    book_ids = view.get_selected_ids()

    if not book_ids:
        return

    for book_id in book_ids:
        # メタデータの事をCalibreでは"mi"と略すのが定番
        mi = db.get_metadata(book_id, index_is_id=True)

        # 処理
        old_title = mi.title
        old_series = mi.series
        new_title = convert_text(mi.title)
        new_series = convert_text(mi.series)

        # 後処理：変更があった場合のみ保存
        changed: bool = False
        if new_title != old_title:
            mi.title = new_title
            changed = True
        if new_series != old_series:
            mi.series = new_series
            changed = True

        if changed:
            db.set_metadata(
                book_id,
                mi,
                set_title=True,
            )
            print(f'''-----
                normalized.
                ID: {book_id}
                \t TITLE: {old_title}
                \t->\t{new_title}
                \tSERIES: {old_series}
                \t->\t{new_series}
                ''')
    # 実行結果
    print(f'-----\nnormalized selected {len(book_ids)} books.')
    return Result(
        processed=len(book_ids),
        changed=changed,
        source='Normalize'
    )
