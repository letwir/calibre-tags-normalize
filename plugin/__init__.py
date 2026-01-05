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
    version = (1, 1, 0)
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
        menu = self.gui.library_view.menu()

        self.normalize_action = self.create_menu_action(
            menu,
            'normalize_only',
            '正規化',
            triggered=self.func_normalize
        )

        # self.amazon_action = self.create_menu_action(
        #     menu,
        #     'fetch_amazon_and_normalize',
        #     'Amazonから取得して正規化',
        #     triggered=self.func_amazon_fetch
        # )
        ## 選択状態に応じてアクションの有効/無効を切り替え
        self.gui.library_view.selectionModel().selectionChanged.connect(
            self.update_action_state
        )
    # 切り替え機能の処理
    def update_action_state(self, *args):
        enabled = bool(self.gui.library_view.get_selected_ids())
        self.normalize_action.setEnabled(enabled)
    #    self.amazon_action.setEnabled(enabled)
    def genesis(self):
        try:
            # 正規化アクション
            self.qaction.setText('Normalization/正規化')
            self.qaction.triggered.connect(self.func_normalize)
        except Exception:
            pass

    # def location_selected(self, loc):
    #     # Enable the action only when the library view is active
    #     try:
    #         enabled = (loc == 'library')
    #         self.qaction.setEnabled(enabled)
    #     except Exception:
    #         pass

    def initialization_complete(self):
        # Called once GUI is ready; ensure action is in context menus
        try:
            # create_menu_action will add to menus; unique name should be unique
            self.create_menu_action(
                self.gui.library_view.menu(),
                'normalize_fullwidth',
                'Normalize fullwidth numbers',
                triggered=self.func_normalize
                )
            # self.create_menu_action(
            #     self.gui.library_view.menu(),
            #     'fetch_amazon',
            #     'fetch Amazon metaTag',
            #     triggered=self.func_amazon_fetch
            #     )
        except Exception:
            # Fallback: some calibre versions expose different menu APIs
            pass

    def func_normalize(self):
        # Call the helper that implements normalization logic.
        print('Normalize action triggered\n🚀正規化がトリガーされた')
        try:
            from .normalize import normalize_main
            print('...正規化関数実行中')
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

    def func_amazon_fetch(self):
        # Call the helper that implements normalization logic.
        print('Fetch AmazonJP action triggered\n🚀メタ取得がトリガーされた')
        try:
            from .amazon_fetch import amazon_fetch_main
            print('...メタ取得関数実行中')
            result_amazon_fetch = amazon_fetch_main(self.gui)
            print(f'✔メタ取得は為された。\n{result_amazon_fetch.changed}/{result_amazon_fetch.processed}\n-----')
        except Exception as e:
            # Always print exception to stdout for debugging when running
            # calibre-debug so we can see what occurred.
            print('FetchAmazon Exception\n❌️例外発生！:\n', repr(e))
            try:
                from calibre.gui2 import error_dialog
                error_dialog(self.gui, 'Fetch Error', str(e))
            except Exception:
                # If GUI dialog fails, re-raise so the error appears in console
                raise
