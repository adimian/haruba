import blinker

signals = blinker.Namespace()

new_file_or_folder = signals.signal("new-file-or-folder")
browsing = signals.signal("browsing")
