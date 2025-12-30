# amazon_fetch.py
from calibre.ebooks.metadata.sources.amazon_jp import AmazonJP

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
        timeout=30
    )

    if rq.empty():
        return None

    return rq.get()
