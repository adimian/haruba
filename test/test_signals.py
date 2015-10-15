from flask import current_app
from haruba.api import app
from haruba.signals import new_file_or_folder


def test_new_file_or_folder():
    with app.app_context():
        current_app._call_on_me = False

        @new_file_or_folder.connect_via(app)
        def call_on_me(sender, path):
            assert path == "/some/file/path"
            sender._call_on_me = True

        new_file_or_folder.send(current_app._get_current_object(),
                                path="/some/file/path")

        new_file_or_folder.disconnect(call_on_me)
        assert current_app._call_on_me
