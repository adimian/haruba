import os
import shutil
from scandir import scandir
import datetime
from . import ProtectedResource
from flask import abort, request, current_app
from flask_restful import reqparse
from haruba.permissions import has_read, has_write
from haruba.utils import get_group_root, success
from ..signals import browsing
import logging

logger = logging.getLogger(__name__)


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def assemble_directory_contents(group, path):
    group_root = get_group_root(group)
    full_path = os.path.join(group_root, path)
    browsing.send(current_app._get_current_object(),
                  path=full_path)
    if not os.path.exists(full_path):
        logger.error('failed to find on disk: %s' % full_path)
        return abort(404, 'not found on disk: %s' % request.url)

    if not os.path.isdir(full_path):
        return abort(400, "%s is not a folder" % request.url)

    folders = []
    files = []

    url_root = current_app.config['API_URL_PREFIX']

    for item in scandir(full_path):
        stat = item.stat()  # this is a very expensive call, use sparingly
        mod_date = datetime.datetime.fromtimestamp(stat.st_mtime)
        short_path = '/'.join((group, path, item.name)).replace('//', '/')
        d_link = '/'.join((url_root, 'download', short_path))
        uri = '/'.join((url_root, 'files', short_path))
        file_dict = {'name': item.name,
                     'is_file': item.is_file(),
                     'is_dir': item.is_dir(),
                     'download_link': d_link.replace('//', '/'),
                     'uri': uri.replace('//', '/'),
                     'path': short_path.replace('//', '/'),
                     'modif_date': mod_date.strftime('%Y-%m-%d %H:%M:%S')}
        if file_dict['is_dir']:
            file_dict['extension'] = "folder"
            file_dict['size'] = '-'
            file_dict['numeric_size'] = 0
            folders.append(file_dict)
        else:
            size = stat.st_size
            file_dict['size'] = sizeof_fmt(size)
            file_dict['numeric_size'] = size
            file_dict['extension'] = item.name.split(".")[-1]
            files.append(file_dict)
    return folders + files


def delete_file_or_folder(file_or_folder):
    try:
        if os.path.isfile(file_or_folder):
            os.remove(file_or_folder)
        else:
            shutil.rmtree(file_or_folder)
    except Exception:
        return False
    return True


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
        if os.path.exists(new_path):
            abort(400, ("%s already exists at %s"
                        % (new_name, os.path.dirname(path))))
        self.rename(file_path, new_name)
        return success("Successfully renamed to %s" % args['rename_to'])

    def rename(self, path, new_name):
        old_path = path
        new_path = os.path.join(os.path.dirname(path), new_name)
        try:
            os.rename(old_path, new_path)
        except Exception:
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

            if request.content_type == "application/json":
                request.json.pop('files_to_delete', None)
                if request.json:
                    abort(400, "Wrong parameters found, aborting to prevent "
                               "unwanted deletion. Found '%s', the only valid"
                               " key is 'files_to_delete'"
                               % "', '".join(request.json.keys()))
            if request.form:
                abort(400, "Detected form data, aborting to prevent "
                           "unwanted deletion. Please set the content-type "
                           "header to 'application/json' to make your request")

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
