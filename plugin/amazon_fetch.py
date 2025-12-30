#!python3
from time import sleep
import queue
from dataclasses import dataclass   # 実行結果を返すやつ

from calibre.ebooks.metadata.sources.amazon_jp import AmazonJP

# ----- 定数/クラス
REQUEST_INTERVAL = 5.0  # 秒
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

@dataclass(frozen=True)
class Result:
    '''実行結果データクラス'''
    processed: int
    changed: int
    source: str  # 'Normalize' / 'Amazon'


# ----- 関数
def fetch_by_asin(asin, log):
    source = AmazonJP(None)
    rq = queue.Queue()

    source.identify(
        log=log,
        result_queue=rq,
        abort=None,
        identifiers={'mobi-asin': asin},
        title=None,
        authors=None,
        timeout=30,
        ua=UA
    )

    if rq.empty():
        return None

    return rq.get()


def amazon_fetch_main(gui) -> 'Result':
    # gui: calibre.gui2.main.CalibreMain
    db = gui.current_db
    view = gui.library_view
    book_ids = view.get_selected_ids()

    if not book_ids:
        return  # type: ignore

    for book_id in book_ids:
        mi = db.get_metadata(book_id, index_is_id=True)
        asin = mi.get_identifier('mobi-asin')
        if not asin:
            continue

        log = lambda msg: print(f'[{book_id}] {msg}')
        new_mi = fetch_by_asin(asin, log)
        if new_mi:
            # db.set_metadata(book_id, new_mi, index_is_id=True)
            print(book_id, new_mi)
        sleep(REQUEST_INTERVAL)

    return Result(
        processed=len(book_ids),
        changed=0,
        source='Amazon'
    )
