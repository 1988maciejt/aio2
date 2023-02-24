
import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive


class TuiFile(TextualApp.App):
    def compose(self):
        yield TextualWidgets.Header()
        yield TextualWidgets.DirectoryTree("./")
        yield TextualWidgets.Footer()
        