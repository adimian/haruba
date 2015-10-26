import os
from scandir import scandir
from .connection import Sender
from haruba.api import app
from haruba.signals import new_file_or_folder, browsing

sender = Sender(app.config)


@new_file_or_folder.connect_via(app)
def newly_created(sender_object, path):
    if os.path.exists(path):
        sender.send([path])


@browsing.connect_via(app)
def browsing(sender_object, path):
    paths = [path]
    if os.path.exists(path):
        for item in scandir(path):
            paths.append(os.path.join(path, item.name))
        sender.send(paths)
