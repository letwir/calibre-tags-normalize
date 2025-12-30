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
    name = 'Normalize Fullwidth Numbers'
    description = 'Normalize fullwidth digits and fullwidth spaces in title/series for selected books'
    author = 'letwir, ChatGPT-5'
    version = (1, 0, 2)
    action_spec = (
        'Normalize fullwidth numbers',
        None,
        'Normalize fullwidth digits and fullwidth spaces to halfwidth in Title/Series',
        None
        )

    def load_actual_plugin(self, gui):
        return Normalize(gui, self.site_customization)

class Normalize(InterfaceAction):
    name = 'Normalize fullwidth numbers'

    # Make this a 'current' action so it acts on the current selection/view
    action_type = 'current'

    def genesis(self):
        # self.qaction is created automatically from action_spec in the base class
        try:
            self.qaction.triggered.connect(self.run_on_selection)
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
                triggered=self.run_on_selection
                )
        except Exception:
            # Fallback: some calibre versions expose different menu APIs
            pass

    def run_on_selection(self):
        # Call the helper that implements normalization logic.
        print('Normalize action triggered\n🚀正規化アクションがトリガーされました')
        try:
            from .normalize import normalize_selection_via_gui
            print('Calling normalize_selection_via_gui...\n関数実行中')
            normalize_selection_via_gui(self.gui)
            print('normalize_selection_via_gui returned\n✔為された。')
        except Exception as e:
            # Always print exception to stdout for debugging when running
            # calibre-debug so we can see what occurred.
            print('Normalize action exception\n❌️例外発生！:', repr(e))
            try:
                from calibre.gui2 import error_dialog
                error_dialog(self.gui, 'Normalize Error', str(e))
            except Exception:
                # If GUI dialog fails, re-raise so the error appears in console
                raise
