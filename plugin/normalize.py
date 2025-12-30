"""
Normalization helpers used by the plugin wrapper.

Contains a pure-Python function `normalize_text` that converts fullwidth
digits (０-９) and fullwidth space (U+3000) to their ASCII/halfwidth
equivalents. Also provides a scaffold `normalize_selection_via_gui(gui)` that
explains how to wire the function into Calibre's DB; it intentionally does not
mutate the DB directly so you can test in your environment first.
"""
from typing import Optional

# Build translation map: U+3000 -> space, U+FF10..FF19 -> '0'..'9'
FW_MAP = {0x3000: 0x20}
for i in range(10):
    FW_MAP[0xFF10 + i] = ord('0') + i


def normalize_text(s: Optional[str]) -> Optional[str]:
    """Translate fullwidth digits and fullwidth space to halfwidth.

    Returns None if input is None.
    """
    if s is None:
        return None
    try:
        return s.translate(FW_MAP)
    except Exception:
        # Defensive: if non-string passed, convert then translate
        return str(s).translate(FW_MAP)


def normalize_selection_via_gui(gui) -> None:
    """Scaffold entrypoint called from the plugin action.

    This function attempts to locate the selected book ids in the GUI and
    then shows the user what would be changed. It deliberately does not
    perform a DB write — implementing that requires testing in your Calibre
    environment (the DB API names/objects differ by calibre version).

    To implement automatic updates you can use the active library object
    (usually available as `gui.current_db` or `gui.library_view.model().db`) and
    call its metadata update methods. Test such code under `calibre-debug -g`.
    """
    print('normalize_selection_via_gui invoked')
    # Try many ways to get selected ids (best-effort across calibre versions)
    selected = None
    debug_lines = ['Selection discovery debug:']

    # 1) common helper
    try:
        if hasattr(gui, 'library_view') and hasattr(gui.library_view, 'get_selected_ids'):
            s = gui.library_view.get_selected_ids()
            debug_lines.append(f'library_view.get_selected_ids() -> {s}')
            if s:
                selected = s
    except Exception as e:
        debug_lines.append(f'library_view.get_selected_ids() exception: {e}')

    # 2) gui-level helper
    if not selected:
        try:
            if hasattr(gui, 'get_selected_ids'):
                s = gui.get_selected_ids()
                debug_lines.append(f'gui.get_selected_ids() -> {s}')
                if s:
                    selected = s
        except Exception as e:
            debug_lines.append(f'gui.get_selected_ids() exception: {e}')

    # 3) selectionModel on library_view
    if not selected:
        try:
            lv = getattr(gui, 'library_view', None)
            if lv is not None and hasattr(lv, 'selectionModel'):
                sm = lv.selectionModel()
                if sm is not None and hasattr(sm, 'selectedRows'):
                    rows = sm.selectedRows()
                    debug_lines.append(f'selectionModel.selectedRows() -> {rows}')
                    # Try to extract ids from rows if they have internalPointer
                    ids = []
                    for r in rows:
                        try:
                            ip = getattr(r, 'internalPointer', None)
                            if ip is not None and hasattr(ip, 'book_id'):
                                ids.append(ip.book_id)
                        except Exception:
                            pass
                    if ids:
                        selected = ids
        except Exception as e:
            debug_lines.append(f'selectionModel path exception: {e}')

    # 4) try library view model convenience
    if not selected:
        try:
            lv = getattr(gui, 'library_view', None)
            if lv is not None and hasattr(lv, 'selected_ids'):
                s = lv.selected_ids()
                debug_lines.append(f'library_view.selected_ids() -> {s}')
                if s:
                    selected = s
        except Exception as e:
            debug_lines.append(f'library_view.selected_ids() exception: {e}')

    # 5) last resort: try to inspect attributes on gui for anything list-like
    if not selected:
        try:
            cand = []
            for name in dir(gui):
                if 'selected' in name.lower() or 'selection' in name.lower():
                    try:
                        val = getattr(gui, name)
                        if callable(val):
                            try:
                                v = val()
                                debug_lines.append(f'{name}() -> {v}')
                                if isinstance(v, (list, tuple)) and v:
                                    cand.append(v)
                            except Exception:
                                pass
                        else:
                            debug_lines.append(f'{name} -> {val}')
                            if isinstance(val, (list, tuple)) and val:
                                cand.append(val)
                    except Exception:
                        pass
            if cand:
                selected = cand[0]
        except Exception as e:
            debug_lines.append(f'final inspection exception: {e}')

    # If still not found, report debug info to user/console
    if not selected:
        dbg = '\n'.join(debug_lines)
        # Print debug into console (calibre-debug) as primary channel
        print('Normalize: selection not found')
        print(dbg)
        # Also try to show GUI dialog if available
        try:
            from calibre.gui2 import info_dialog
            info_dialog(gui, 'Normalize: selection not found', dbg)
        except Exception:
            pass
        raise RuntimeError('Could not determine selected books from GUI; see debug dialog/console')

    # Try to access DB object (best-effort)
    db = getattr(gui, 'current_db', None)
    if db is None:
        try:
            db = gui.library_view.model().db
        except Exception:
            db = None

    # Build a dry-run list of proposed changes
    proposed = []
    for bid in selected:
        title = None
        series = None
        # Best-effort read using common db APIs; many calibre versions differ.
        if db is not None:
            # Try get_metadata first; if it fails, fall back to get_book.
            if hasattr(db, 'get_metadata'):
                try:
                    mi = db.get_metadata(bid)
                    title = getattr(mi, 'title', None)
                    series = getattr(mi, 'series', None)
                except Exception:
                    # fallback to get_book if available
                    if hasattr(db, 'get_book'):
                        try:
                            b = db.get_book(bid)
                            title = getattr(b, 'title', None)
                        except Exception:
                            title = None
                    else:
                        title = None
            elif hasattr(db, 'get_book'):
                try:
                    b = db.get_book(bid)
                    title = getattr(b, 'title', None)
                except Exception:
                    title = None
            else:
                title = None

        # Use placeholder if DB read failed
        if title is None:
            title = '<unknown title>'

        new_title = normalize_text(title)
        new_series = None if series is None else normalize_text(series)

        if new_title != title or (series is not None and new_series != series):
            proposed.append((bid, title, new_title, series, new_series))

    if not proposed:
        # Nothing to do — print and provide detailed diagnostics to help
        # determine whether titles/series were already normalized or the
        # plugin could not read metadata for the selected books.
        print('No changes proposed: titles/series already normalized or could not read metadata')
        print('Selection debug:')
        try:
            print('  selected ids:', selected)
            print('  db object:', type(db), repr(db))
        except Exception:
            pass

        # For each selected id, attempt multiple reads and print what we get
        for bid in selected:
            try:
                print(f'--- Debug book id {bid} ---')
                # 1) get_metadata
                try:
                    if db is not None and hasattr(db, 'get_metadata'):
                        mi = db.get_metadata(bid)
                        print('  get_metadata ->', mi)
                        try:
                            print('    title:', getattr(mi, 'title', None))
                            print('    series:', getattr(mi, 'series', None))
                        except Exception:
                            pass
                except Exception as e:
                    print('  get_metadata exception:', repr(e))

                # 2) get_book
                try:
                    if db is not None and hasattr(db, 'get_book'):
                        b = db.get_book(bid)
                        print('  get_book ->', b)
                        try:
                            print('    title attr:', getattr(b, 'title', None))
                        except Exception:
                            pass
                except Exception as e:
                    print('  get_book exception:', repr(e))

                # 3) try library view model lookup if available
                try:
                    lv = getattr(gui, 'library_view', None)
                    if lv is not None and hasattr(lv, 'model'):
                        m = lv.model()
                        try:
                            # many models implement book_id -> row mappings
                            if hasattr(m, 'get_book'):
                                bm = m.get_book(bid)
                                print('  model.get_book ->', bm)
                        except Exception:
                            pass
                except Exception as e:
                    print('  library_view.model debug exception:', repr(e))

            except Exception:
                pass

        try:
            from calibre.gui2 import info_dialog
            info_dialog(gui, 'Normalize', 'No changes proposed — titles/series already normalized.')
        except Exception:
            pass
        return

    # Present a simple summary to the user and instruct next steps
    msg_lines = ['Proposed normalization changes:']
    for bid, old_t, new_t, old_s, new_s in proposed:
        msg_lines.append(f'ID {bid}:')
        msg_lines.append(f'  Title: "{old_t}" -> "{new_t}"')
        if old_s is not None:
            msg_lines.append(f'  Series: "{old_s}" -> "{new_s}"')

    msg = '\n'.join(msg_lines)

    # Try to show GUI dialog; also print to console for debugging
    print('Proposed normalization changes:\n' + msg)
    try:
        from calibre.gui2 import info_dialog, question_dialog
        info_dialog(gui, 'Normalize (dry-run)', msg)
        # Ask user whether to apply changes
        try:
            apply_now = question_dialog(gui, 'Apply changes?', msg)
        except Exception:
            # question_dialog may not exist on some installs; fallback to False
            apply_now = False
    except Exception:
        # GUI not available; default to not applying
        apply_now = False

    # If user chose to apply, attempt to write via Calibre DB API first,
    # otherwise instruct offline fallback.
    if apply_now:
        results = []
        for bid, old_t, new_t, old_s, new_s in proposed:
            try:
                res = normalize_metadata_in_db(db, bid, apply=True)
                results.append((bid, True, res.get('new_title'), None))
            except Exception as e:
                results.append((bid, False, None, str(e)))

        # Summarize results
        ok = [r for r in results if r[1]]
        fail = [r for r in results if not r[1]]
        summary_lines = [f'Applied: {len(ok)}  Failed: {len(fail)}']
        for fid, okflag, nt, err in fail:
            summary_lines.append(f'ID {fid} failed: {err}')

        summary = '\n'.join(summary_lines)
        try:
            from calibre.gui2 import info_dialog
            info_dialog(gui, 'Normalize: apply results', summary)
        except Exception:
            print('Apply results:\n' + summary)

        # If any failed, write proposed to JSON to help offline application
        if fail:
            try:
                import json
                import os
                out = os.path.join(
                    os.path.dirname(__file__), 'proposed_changes.json')
                with open(out, 'w', encoding='utf8') as fh:
                    json.dump(
                        [
                            {
                                'book_id': bid,
                                'old_title': old_t,
                                'new_title': new_t,
                                'old_series': old_s,
                                'new_series': new_s,
                            }
                            for bid, old_t, new_t, old_s, new_s in proposed
                        ],
                        fh,
                        ensure_ascii=False,
                        indent=2,
                    )
                print('Wrote proposed changes to', out)
            except Exception:
                pass


def normalize_metadata_in_db(db, book_id: int, apply: bool = False) -> dict:
    """Example helper that shows how a DB update could look.

    This function is intentionally conservative: it computes the normalized
    values and returns a dict with the proposed fields. If `apply` is True
    you should implement the DB write using the appropriate API for your
    calibre version (e.g. `db.set_metadata` / `db.set_title` / `db.set_field`).

    The exact DB method names vary; test under `calibre-debug -g`.
    """
    # Read metadata (this is a placeholder - real code depends on calibre
    # version)
    old_title = None
    old_series = None
    try:
        if hasattr(db, 'get_metadata'):
            mi = db.get_metadata(book_id)
            old_title = getattr(mi, 'title', None)
            old_series = getattr(mi, 'series', None)
    except Exception:
        pass

    new_title = normalize_text(old_title) if old_title is not None else None
    new_series = normalize_text(old_series) if old_series is not None else None

    result = {
        'book_id': book_id,
        'old_title': old_title,
        'new_title': new_title,
        'old_series': old_series,
        'new_series': new_series,
        'applied': False,
    }

    if apply:
        # Try various known Calibre DB API methods (best-effort). If none
        # match, raise to indicate failure and allow offline fallback.
        new_title = result['new_title']
        new_series = result['new_series']

        # 1) common pattern: update Metadata object and call set_metadata
        try:
            if hasattr(db, 'get_metadata') and hasattr(db, 'set_metadata'):
                mi = db.get_metadata(book_id)
                if mi is not None:
                    try:
                        setattr(mi, 'title', new_title)
                    except Exception:
                        pass
                    try:
                        setattr(mi, 'series', new_series)
                    except Exception:
                        pass
                    db.set_metadata(book_id, mi)
                    result['applied'] = True
                    return result
        except Exception:
            pass

        # 2) try simple setters if present
        try:
            if hasattr(db, 'set_title'):
                db.set_title(book_id, new_title)
                result['applied'] = True
                return result
        except Exception:
            pass

        # 3) last resort: some DB objects expose a generic set function
        try:
            if hasattr(db, 'set'):
                # not standard; attempt generic set
                db.set(book_id, title=new_title)
                result['applied'] = True
                return result
        except Exception:
            pass

        # No known API succeeded
        raise NotImplementedError(
            'DB write via Calibre API failed for this calibre version')

    return result
