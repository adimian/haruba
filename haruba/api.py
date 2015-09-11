import json
import logging
import os
from os.path import isfile
import shutil

from flask import current_app, session, send_file, request, abort
from flask_login import LoginManager
from flask_login import login_required, login_user, current_user, logout_user
from flask_principal import Identity, identity_changed
from flask_restful import Resource, reqparse, inputs
from sigil_client import SigilClient
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import FileStorage
from collections import defaultdict

from .database import db, Zone
from .permissions import (has_read, has_write, has_admin_read,
                          has_admin_write, declare_zone_permissions,
                          retract_zone_permissions, ZONE_CONTEXT)
from .utils import (User, assemble_directory_contents, get_group_root,
                    success, unzip,
                    make_zip, make_selective_zip, delete_file_or_folder,
                    get_path_from_group_url, construct_available_path,
                    prep_json, get_sigil_client)


logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

login_manager = LoginManager()


def request_authentication(username, password):
    api_url = current_app.config['SIGIL_API_URL']
    app_name = current_app.config['SIGIL_APP_NAME']
    client = SigilClient(api_url, username=username, password=password)
    client.login()
    session['sigil_token'] = client._token
    details = client.user_details()
    details.update(client.provides(context=app_name))
    return details


@login_manager.user_loader
def load_user(login):
    return User(login, {})


class Login(Resource):
    def get(self):
        # for the JS lib to know if the user is logged in or not
        return current_user.is_authenticated()

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('login', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        login = args['login']
        user = request_authentication(login, args['password'])
        if user.get('username'):
            login_user(User(user['username'], user['provides']))
            session['provides'] = user['provides']
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(login))
            return ("success", 200)
        abort(401, "Could not log in")


class ProtectedResource(Resource):
    method_decorators = [login_required]


class ProtectedReadResource(Resource):
    method_decorators = [login_required, has_read]


class ProtectedWriteResource(Resource):
    method_decorators = [login_required, has_write]


class ProtectedAdminReadResource(Resource):
    method_decorators = [login_required, has_admin_read]


class ProtectedAdminWriteResource(Resource):
    method_decorators = [login_required, has_admin_write]


class Logout(ProtectedResource):
    def get(self):
        logout_user()


class Folder(ProtectedResource):
    @has_read
    def get(self, group, group_root, path=""):
        """
        returns a list of files and directories at the given path
        """
        return assemble_directory_contents(group, path)

    @has_write
    def post(self, group, group_root, path=""):
        """
        creates a folder at the give path
        """
        root = get_group_root(group)
        parent = os.path.dirname(path)
        full_parent_path = os.path.join(root, parent)
        full_path = os.path.join(root, path)

        if not os.path.exists(full_parent_path):
            abort(400, "%s does not exist" % parent)
        if os.path.exists(full_path):
            abort(400, "%s already exists" % path)

        os.mkdir(os.path.join(root, path))
        message = "Successfully created folder '%s'" % os.path.basename(path)
        return success(message)

    @has_write
    def put(self, group, group_root, path=""):
        """
        renames a file or folder at a given path
        """
        parser = reqparse.RequestParser()
        parser.add_argument('rename_to', type=str, required=True)
        args = parser.parse_args()

        new_name = args['rename_to']
        file_path = os.path.join(group_root, path)
        if not os.path.exists(file_path):
            abort(400, "%s does not exist" % path)

        new_path = os.path.join(os.path.dirname(file_path), new_name)
        print(new_path)
        if os.path.exists(new_path):
            abort(400, ("%s already exists at %s"
                        % (new_name, os.path.dirname(path))))
        self.rename(file_path, new_name)
        return success("Successfully renamed to %s" % args['rename_to'])

    def rename(self, path, new_name):
        old_path = path
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(new_path):
            abort(400, "%s already exists." % request.url)
        else:
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print(e)
                abort(400, "Could not rename %s" % request.url)

    @has_write
    def delete(self, group, group_root, path=""):
        """
        deletes if the given path is a file
        if the given path is a folder, it will check for request data
        if there is data, the files given in the data will be deleted
        if there is no data, the folder is deleted
        """
        full_path = os.path.join(group_root, path)
        if not os.path.exists(full_path):
            abort(400, "%s does not exist" % path)
        if os.path.isfile(full_path):
            if not delete_file_or_folder(full_path):
                message = "Could not delete: %s" % os.path.basename(full_path)
                abort(400, message)
        else:
            parser = reqparse.RequestParser()
            parser.add_argument('files_to_delete', type=list, location='json')
            args = parser.parse_args()

            undeleted_files = []
            if args['files_to_delete']:
                for filename in args['files_to_delete']:
                    filepath = os.path.join(full_path, filename)
                    if not delete_file_or_folder(filepath):
                        undeleted_files.append(os.path.basename(full_path))
            else:
                if not delete_file_or_folder(full_path):
                    undeleted_files.append(os.path.basename(full_path))
            if undeleted_files:
                message = "Could not delete: %s" % ", ".join(undeleted_files)
                abort(400, message)
        return success("Successfully deleted %s" % path)


class MyZones(ProtectedResource):
    def get(self):
        client = get_sigil_client()
        app_name = current_app.config['SIGIL_APP_NAME']
        session['provides'] = client.provides(context=app_name)['provides']
        zones = []
        for key, values in current_user.zones.items():
            zones.append({"zone": key, "access": values})
        return zones


class Upload(ProtectedWriteResource):
    def post(self, group, group_root, path=""):
        """
        allows to upload one or more files to the given path
        """
        parser = reqparse.RequestParser()
        parser.add_argument('files', type=FileStorage, location='files',
                            action='append', default=[])
        parser.add_argument('unpack_zip', type=inputs.boolean, default=False)
        parser.add_argument('delete_zip_after_unpack', type=inputs.boolean,
                            default=False)
        args = parser.parse_args()

        full_path = os.path.join(group_root, path)
        if not os.path.isdir(full_path):
            abort(400, "%s is not a folder" % request.url)
        for filestorage in args['files']:
            file_name = filestorage.filename
            file_path = os.path.join(full_path, file_name)

            with open(file_path, "wb+") as fh:
                fh.write(filestorage.read())

            if args['unpack_zip'] and file_name.endswith(".zip"):
                unzip(file_path, full_path, args['delete_zip_after_unpack'])

        message = "Successfully uploaded to '%s'" % os.path.basename(path)
        return success(message)


class Download(ProtectedReadResource):
    def get(self, group, group_root, path=""):
        """
        downloads the file or folder at the given path
        """
        print("in single download")
        filepath = os.path.join(group_root, path)
        if not os.path.exists(filepath):
            abort(404, 'Not Found: %s' % request.url)

        if not isfile(filepath):
            filepath = make_zip(filepath, filepath)

        return send_file(filepath,
                         as_attachment=True,
                         attachment_filename=os.path.basename(filepath))

    def post(self, group, group_root, path=""):
        """
        creates a zip with the selected files and folders at the given path
        and puts it up for download
        """
        print("in multi download")
        parser = reqparse.RequestParser()
        parser.add_argument('filenames', action='append', required=True)
        args = parser.parse_args()

        zip_name = group
        if path:
            zip_name = os.path.basename(path)

        # parse potential browser form data
        if len(args['filenames']) == 1:
            args['filenames'] = args['filenames'][0].split(",")

        base_path = os.path.join(group_root, path)
        files = []
        for filename in args['filenames']:
            print(filename)
            filepath = os.path.join(base_path, filename)
            do_not_exist = []
            if not os.path.exists(filepath):
                do_not_exist.append(filename)
            files.append(filepath)
            if do_not_exist:
                message = "Following files could not be found at %s: %s"
                abort(400, message % (request.url,
                                      ", ".join(do_not_exist)))

        filepath = make_selective_zip(zip_name, base_path, files)
        return send_file(filepath,
                         as_attachment=True,
                         attachment_filename=os.path.basename(filepath))


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
            command['to'] = get_path_from_group_url(command['to'])
        else:
            original_path = request.path
            command['to'] = full_path
        if not os.path.exists(command['to']):
            abort(400, "%s does not exist" % original_path)
        return command

    def perpare_copy_cut(self, command, func):
        destination_folder = command['to']
        if not os.path.isdir(destination_folder):
            abort(400, "%s must be a directory" % destination_folder)

        for copy_file in command['from']:
            filepath_from = get_path_from_group_url(copy_file)
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


class Zones(ProtectedResource):
    @has_admin_read
    def get(self):
        zones = db.session.query(Zone).all()
        return_list = []
        for zone in zones:
            return_list.append({'id': zone.id,
                                'name': zone.name,
                                'path': zone.path})
        return return_list

    @has_admin_write
    def post(self):
        """
        create zones
        [{'zone': <zone_name>,
          'path': <path_extension>},
          {'zone': <zone_name>,
          'path': <path_extension>},]
        """
        parser = reqparse.RequestParser()
        parser.add_argument('zones', location='json', type=prep_json)
        args = parser.parse_args()
        print(args)
        if not args['zones']:
            abort(400, "No zones found")

        zones = []
        for zone in args["zones"]:
            print(zone)
            name = zone.get('zone')
            path = zone.get('path')
            if not name or not path:
                abort(400, "A zone entry needs a zone and path key.")
            if db.session.query(Zone).filter_by(name=name).all():
                abort(400, "This zone already exists")
            if path.startswith("/"):
                path = path[1:]
            zone_path = os.path.join(current_app.config['HARUBA_SERVE_ROOT'],
                                     path)
            try:
                declare_zone_permissions(name)
            except Exception as e:
                abort(400, str(e))
            os.makedirs(zone_path, exist_ok=True)
            zones.append(name)
            zone = Zone(name, path)
            db.session.add(zone)
            db.session.commit()
        return success("Successfully created zones: %s"
                             % ", ".join(zones))

    @has_admin_write
    def put(self):
        """
        update zones
        [{'id': <zone_id>,
          'zone': <zone_name>,
          'path': <path_extension>},
         {'id': <zone_id>,
          'zone': <zone_name>,
          'path': <path_extension>},]
        """
        parser = reqparse.RequestParser()
        parser.add_argument('zones', location='json', type=prep_json)
        parser.add_argument('create_if_not_exists', type=inputs.boolean,
                            default=False)
        args = parser.parse_args()

        zones = []
        for z in args["zones"]:
            if not z.get('id'):
                abort(400, "must provide a zone id")
            try:
                zone = db.session.query(Zone).filter_by(id=z['id']).one()
                dbzone = db.session.query(Zone).filter_by(name=z['zone']).all()
                if z.get('zone') and dbzone:
                    abort(400, "This zone already exists")
                old_name = zone.name
                zone.name = z.get('zone', zone.name)
                path = z.get('path', zone.path)
                if path.startswith("/"):
                    path = path[1:]
                zone.path = path
            except NoResultFound:
                msg = ("Zone id '%s' does not exist" % z['id'])
                abort(400, msg)

            if not old_name == zone.name:
                try:
                    retract_zone_permissions(old_name)
                    declare_zone_permissions(zone.name)
                except Exception as e:
                    abort(400, str(e))
            zone_path = os.path.join(current_app.config['HARUBA_SERVE_ROOT'],
                                     zone.path)
            os.makedirs(zone_path, exist_ok=True)
            db.session.add(zone)
            zones.append(zone.name)
            db.session.commit()
        return success("Successfully updated zones: %s"
                             % ", ".join(zones))


class Permissions(ProtectedResource):
    @has_admin_read
    def get(self):
        client = get_sigil_client()
        app_name = current_app.config['SIGIL_APP_NAME']
        try:
            users = client.list_users(context=app_name)
            # TODO: needs to be replaced by the newly implemented search
            # function in sigil
            for user in users['users']:
                permissions = client.provides(context=app_name,
                                              username=user['username'])
                zone_permissions = defaultdict(list)
                for permission in permissions['provides']:
                    perm = list(permission)
                    if perm[0] == ZONE_CONTEXT:
                        zone_permissions[perm[2]].append(perm[1])
                user['permissions'] = zone_permissions
        except Exception as e:
            abort(400, str(e))
        return users

    @has_admin_write
    def post(self):
        """
        grants needs
        {'permissions': [{'username': <username>,
                          'needs': [<need>, <need>]},]}
        """
        return self.prepare_request('grant')

    @has_admin_write
    def delete(self):
        """
        deletes needs
        {'permissions': [{'username': <username>,
                          'needs': [<need>, <need>]},]}
        """
        return self.prepare_request('withdraw')

    def prepare_request(self, func_name):
        parser = reqparse.RequestParser()
        parser.add_argument('permissions', location='json', type=prep_json)
        args = parser.parse_args()

        if not args['permissions']:
            abort(400, "No permissions found")
        client = get_sigil_client()
        app_name = current_app.config['SIGIL_APP_NAME']

        for perm in args['permissions']:
            print(perm)
            if not isinstance(perm, dict):
                abort(400, "A need item must be a dictionary")
            username = perm.get('username')
            needs = perm.get('needs')
            if not username and not needs:
                msg = "A need item must have a 'username' and 'needs' key"
                abort(400, msg)
            try:
                func = getattr(client, func_name)
                print(needs)
                print(func(context=app_name, needs=needs, username=username))
            except Exception as e:
                print(e)
                abort(400, str(e))
        return success("Success")
