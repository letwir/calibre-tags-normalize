"""
Calibre plugin wrapper (InterfaceActionBase)

Scaffold plugin that wires a GUI action to the normalization helper in
`normalize.py`. The heavy DB integration is left intentionally minimal
so it can be iterated safely while testing inside calibre.
"""
# Calibre GUIプラグイン基底クラス
from calibre.customize import InterfaceActionBase
from calibre.gui2.actions import InterfaceAction

# ---- プラグイン本体の説明 ----
class NormalizeBase(InterfaceActionBase):
    name = 'Normalize Fullwidth'
    description = '''
    Normalize fullwidth digit, number, space and etc...
    in title/series for selected books
    '''
    author = 'letwir, ChatGPT-5'
    version = (1, 0, 2)
    action_spec = (
        'Normalize Fullwidth for Title/Series',
        None,
        'Normalize Fullwidth for Title/Series',
        None
        )
    def load_actual_plugin(self, gui):
        return Normalize(gui, self.site_customization)

class Normalize(InterfaceAction):
    name = 'Normalize fullwidth'
    # current: GUIで選択した本に対して動作
    action_type = 'current'

    # ----- ✨️ここがGUIの可視化部分✨️ -----
    def genesis(self):
        try:
            # 正規化アクション
            self.qaction.setText('Normalization/正規化')
            self.qaction.triggered.connect(self.func_normalize)
        except Exception:
            pass

        try:
            self.qaction.setText('Fetch Amazon metaTag/Amazonメタ情報取得')
            self.qaction.triggered.connect(self.func_amazon)
        except Exception:
            pass

    def location_selected(self, loc):
        # Enable the action only when the library view is active
        try:
            enabled = (loc == 'library')
            self.qaction.setEnabled(enabled)
        except Exception:
            pass

    def initialization_complete(self):
        # Called once GUI is ready; ensure action is in context menus
        try:
            # create_menu_action will add to menus; unique name should be unique
            self.create_menu_action(
                self.gui.library_view.menu(),
                'normalize_fullwidth_numbers_context',
                'Normalize fullwidth numbers',
                triggered=self.func_normalize
                )
        except Exception:
            # Fallback: some calibre versions expose different menu APIs
            pass

    def func_normalize(self):
        # Call the helper that implements normalization logic.
        print('Normalize action triggered\n🚀正規化がトリガーされた')
        try:
            from .normalize import normalize_main
            print('…正規化関数実行中')
            result_normalize = normalize_main(self.gui)
            print(f'✔正規化は為された。\n{result_normalize.changed}/{result_normalize.processed}\n-----')
        except Exception as e:
            # Always print exception to stdout for debugging when running
            # calibre-debug so we can see what occurred.
            print('Normalize Exception\n❌️例外発生！:\n', repr(e))
            try:
                from calibre.gui2 import error_dialog
                error_dialog(self.gui, 'Normalize Error', str(e))
            except Exception:
                # If GUI dialog fails, re-raise so the error appears in console
                raise
