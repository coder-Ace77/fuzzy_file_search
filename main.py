# textual_file_search/main.py

from apps.fuzzy_file_search import FileSearchApp

if __name__ == "__main__":
    app = FileSearchApp()
    app.run()