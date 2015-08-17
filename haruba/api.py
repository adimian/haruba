import logging
import os
from os.path import isfile
import shutil

from flask import current_app, session, send_file, request
from flask_login import login_required, login_user
from flask_restful import Resource, Api, reqparse, inputs
from flask_login import LoginManager
from flask_principal import Identity, identity_changed
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import FileStorage

from haruba.utils import (User, assemble_directory_contents, get_group_root,
                          throw_success, throw_error, throw_not_found, unzip,
                          make_zip, make_selective_zip, delete_file_or_folder,
                          get_path_from_group_url, construct_available_path,
                          throw_unauthorised)
from haruba.permissions import (has_read, has_write, has_admin_read,
                                has_admin_write)
from haruba.database import db, Zone


logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

haruba_api = Api()
login_manager = LoginManager()


def request_authentication(username, password):
    # connect to identity server and authenticate the user
    return {'login': 'maarten',
            'givenName': 'de paepe',
            'displayName': 'Maarten De Paepe',
            'provides': [['zone', 'read', 'pyrene_prod'],
                         ['zone', 'write', 'pyrene_prod']]
            }


@login_manager.user_loader
def load_user(login):
    return User(login, {})


class Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('login', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        login = args['login']
        user = request_authentication(login, args['password'])
        if user.get('login'):
            login_user(User(user['login'], user['provides']))
            session['provides'] = user['provides']
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(login))
            return throw_success("Success")
        return throw_unauthorised("Could not log in")


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
            return throw_error("%s does not exist" % parent)
        if os.path.exists(full_path):
            return throw_error("%s already exists" % path)

        os.mkdir(os.path.join(root, path))
        message = "Successfully created folder '%s'" % os.path.basename(path)
        return throw_success(message)

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
            return throw_error("%s does not exist" % path)

        new_path = os.path.join(os.path.dirname(file_path), new_name)
        if os.path.exists(new_path):
            return throw_error(("%s already exists at %s"
                                % (new_name, os.path.dirname(path))))
        self.rename(file_path, new_name)
        return throw_success("Successfully renamed to %s" % args['rename_to'])

    def rename(self, path, new_name):
        old_path = path
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(new_path):
            return throw_error("%s already exists." % request.url)
        else:
            try:
                os.rename(old_path, new_path)
            except Exception:
                return throw_error("Could not rename %s" % request.url)

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
            return throw_error("%s does not exist" % path)
        if os.path.isfile(full_path):
            if not delete_file_or_folder(full_path):
                message = "Could not delete: %s" % os.path.basename(full_path)
                return throw_error(message)
        else:
            parser = reqparse.RequestParser()
            parser.add_argument('files_to_delete', action='append', default=[])
            args = parser.parse_args()

            undeleted_files = []
            if args['files_to_delete']:
                for filename in args['files_to_delete']:
                    filepath = os.path.join(full_path, filename)
                    print(filepath)
                    if not delete_file_or_folder(filepath):
                        undeleted_files.append(os.path.basename(full_path))
            else:
                if not delete_file_or_folder(full_path):
                    undeleted_files.append(os.path.basename(full_path))
            if undeleted_files:
                message = "Could not delete: %s" % ", ".join(undeleted_files)
                return throw_error(message)
        return throw_success("Successfully deleted %s" % path)


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
            return throw_error("%s is not a folder" % request.url)
        print(args['files'])
        for filestorage in args['files']:
            file_name = filestorage.filename
            file_path = os.path.join(full_path, file_name)

            with open(file_path, "wb+") as fh:
                fh.write(filestorage.read())

            if args['unpack_zip'] and file_name.endswith(".zip"):
                unzip(file_path, full_path, args['delete_zip_after_unpack'])

        message = "Successfully uploaded to '%s'" % os.path.basename(path)
        return throw_success(message)


class Download(ProtectedReadResource):
    def get(self, group, group_root, path=""):
        """
        downloads the file or folder at the given path
        """
        filepath = os.path.join(group_root, path)
        if not os.path.exists(filepath):
            return throw_not_found()

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
        parser = reqparse.RequestParser()
        parser.add_argument('filenames', action='append', required=True)
        args = parser.parse_args()

        zip_name = "%s.zip" % group
        if path:
            zip_name = "%s.zip" % os.path.basename(path)

        base_path = os.path.join(group_root, path)
        files = []
        for filename in args['filenames']:
            filepath = os.path.join(base_path, filename)
            do_not_exist = []
            if not os.path.exists(filepath):
                do_not_exist.append(filename)
            files.append(filepath)
            if do_not_exist:
                message = "Following files could not be found at %s: %s"
                return throw_error(message % (request.url,
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
        parser.add_argument('commands')
        args = parser.parse_args()

        full_path = os.path.join(group_root, path)
        cmds = {"cut": (self.perpare_copy_cut, {"func": self.handle_cut}),
                "copy": (self.perpare_copy_cut, {"func": self.handle_copy}),
                "unzip": (self.unzip, {})}

        errors = []
        for command in args['commands']:
            if command.get('to'):
                command['to'] = get_path_from_group_url(command['to'])
            else:
                command['to'] = full_path
            if not os.path.exists(command['to']):
                return throw_error("%s does not exist" % command['to'])

            cmd = command.get('type', '').lower()
            if not cmd:
                return throw_error("Must provide a command type")

            try:
                func, params = cmds[cmd]
            except KeyError:
                return throw_error("'%s' is not a valid comand" % cmd)

            func(command, errors, **params)

            if errors:
                message = "Following errors happened: %s" % ", ".join(errors)
                return throw_error(message)
        return throw_success("Successfully executed commands")

    def perpare_copy_cut(self, command, errors, func):
        destination_folder = command['to']
        if not os.path.isdir(destination_folder):
            errors.append("%s must be a directory" % destination_folder)

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

    def unzip(self, command, errors):
        path = command['to']
        if not path.endswith('.zip'):
            errors.append("%s is not a valid zipfile" % request.url)
        unzip(path, os.path.dirname(path),
              command.get('delete_zip_after_unpack', False))


class Zone(ProtectedResource):
    @has_admin_read
    def get(self):
        zones = db.session.query(Zone).all()
        return_list = []
        for zone in zones:
            return_list.append({'name': zone.name, "path": zone.path})
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
        parser.add_argument('zones')
        args = parser.parse_args()
        if not args['zones']:
            throw_error("No zones found")

        for zone in args["zones"]:
            name = zone.get('name')
            path = zone.get('path')
            if not name or not path:
                throw_error("A zone entry needs a zone and path key.")
            zone = Zone(name, path)
            db.session.add(zone)
            db.session.commit()
        zones = list(args['zones'].keys())
        throw_success("Successfully created zones: %s" % ", ".join(zones))

    @has_admin_write
    def put(self):
        """
        update zones
        [{'zone': <zone_name>,
          'path': <path_extension>},
          {'zone': <zone_name>,
          'path': <path_extension>},]
        """
        parser = reqparse.RequestParser()
        parser.add_argument('zones')
        parser.add_argument('create_if_not_exists', type=inputs.boolean,
                            default=False)
        args = parser.parse_args()

        for zone in args["zones"]:
            name = zone.get('name')
            path = zone.get('path')
            if not name or not path:
                throw_error("A zone entry needs a zone and path key.")
            try:
                zone = db.session.query(Zone).filter_by(name=name).one()
                zone.name = name
                zone.path = path
            except NoResultFound:
                if args['create_if_not_exists']:
                    zone = Zone(name, path)
                else:
                    msg = ("Zone %s does not exist, set 'create_if_not_exists'"
                           " to true if you want to create" % name)
                    throw_error(msg)
            db.session.add(zone)
            db.session.commit()
        zones = args['zones'].keys()
        throw_success("Successfully updated zones: %s" % ", ".join(zones))


haruba_api.add_resource(Login,
                        '/login')
haruba_api.add_resource(Folder,
                        '/files/<group>',
                        '/files/<group>/<path:path>')
haruba_api.add_resource(Upload,
                        '/upload/<group>',
                        '/upload/<group>/<path:path>')
haruba_api.add_resource(Download,
                        '/download/<group>',
                        '/download/<group>/<path:path>')
haruba_api.add_resource(Command,
                        '/command/<group>',
                        '/command/<group>/<path:path>')
