import os
import json
import shutil
from flask import abort, request
from flask_restful import reqparse
from flask_principal import Permission
from haruba.endpoints import ProtectedWriteResource
from haruba.utils import success, unzip, get_group_root, prep_json
from ..permissions import ZONE_CONTEXT, READ_PERMISSION, WRITE_PERMISSION


def get_path_from_group_url(url):
    if url.startswith("/"):
        url = url[1:]
    split = url.split("/")
    group = split[0]
    path = split[1:]
    return os.path.join(get_group_root(group), *path), group


def construct_available_path(filepath_from, destination_folder):
    if os.path.exists(filepath_from):
        filepath_to = os.path.join(destination_folder,
                                   os.path.basename(filepath_from))
        i = 1
        if os.path.exists(filepath_to):
            fnn = "%s(%s)" % (filepath_to, i)
            while os.path.exists(fnn):
                i += 1
                fnn = "%s(%s)" % (filepath_to, i)
            filepath_to = fnn
        return filepath_to
    abort(400, "Path does not exist")


def can_read(group):
    permission = Permission((ZONE_CONTEXT, READ_PERMISSION, group))
    if not permission.can():
        abort(401, "You are not allowed to read in zone '%s'" % group)


def can_write(group):
    permission = Permission((ZONE_CONTEXT, WRITE_PERMISSION, group))
    if not permission.can():
        abort(401, "You are not allowed to write in zone '%s'" % group)


class Command(ProtectedWriteResource):
    def post(self, group, group_root, path=""):
        """
        Currently used for copy and cut actions.
        Could potentially be expanded to have more commands
        input:
        [{'type': 'cut',
          'from': ["/group/some/folder",
                   "/group/another/folder"],
          'to': "/group/destination/folder"},
         {'type': 'copy',
          'from': ["/group/yet_another/folder"],
          'to': "/group/another_destination/folder"},
         {'type': 'unzip',
          'delete_zip_after_unpack': True}]
        """
        parser = reqparse.RequestParser()
        parser.add_argument('commands', location='json', type=prep_json)
        args = parser.parse_args()

        full_path = os.path.join(group_root, path)
        cmds = {"cut": (self.perpare_copy_cut, {"func": self.handle_cut}),
                "copy": (self.perpare_copy_cut, {"func": self.handle_copy}),
                "unzip": (self.unzip, {})}

        for command in args['commands']:
            command = self.prepare_command(command, full_path)

            cmd = command.get('type', '').lower()
            if not cmd:
                abort(400, "Must provide a command type")

            try:
                func, params = cmds[cmd]
            except KeyError:
                abort(400, "'%s' is not a valid comand" % cmd)

            func(command, **params)

        return success("Successfully executed commands")

    def prepare_command(self, command, full_path):
        msg = "Input must be a dict containing 'type' and 'from' keys"
        if isinstance(command, str):
            try:
                command = json.loads(command)
            except ValueError:
                abort(400, "%s, not string" % msg)
        if not isinstance(command, dict):
            abort(400, "%s, not %s" % (msg, type(command).__name__))

        if command.get('to'):
            original_path = command['to']
            command['to'], group = get_path_from_group_url(command['to'])
            # check if we can write to this group
            can_write(group)
        else:
            # no need to check if we can write.
            # ProtectedView has already done this
            original_path = request.path
            command['to'] = full_path

        if command.get('from'):
            for copy_file in command['from']:
                _, group = get_path_from_group_url(copy_file)
                can_read(group)

        if not os.path.exists(command['to']):
            abort(400, "%s does not exist" % original_path)
        return command

    def perpare_copy_cut(self, command, func):
        destination_folder = command['to']
        if not os.path.isdir(destination_folder):
            abort(400, "%s must be a directory" % request.path)

        print("check from")
        if not command.get('from'):
            abort(400, "To copy or cut you must provide a 'from' key")
        print("checked from")

        for copy_file in command['from']:
            filepath_from, _ = get_path_from_group_url(copy_file)
            filepath_to = construct_available_path(filepath_from,
                                                   destination_folder)
            func(filepath_from, filepath_to)

    def handle_cut(self, filepath_from, filepath_to):
        shutil.move(filepath_from, filepath_to)

    def handle_copy(self, filepath_from, filepath_to):
        if os.path.isdir(filepath_from):
            shutil.copytree(filepath_from, filepath_to)
        else:
            shutil.copy(filepath_from, filepath_to)

    def unzip(self, command):
        path = command['to']
        if not path.endswith('.zip'):
            abort(400, "%s is not a valid zipfile" % request.url)
        unzip(path, os.path.dirname(path),
              command.get('delete_zip_after_unpack', False))
