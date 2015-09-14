import os
import shutil
from scandir import scandir
from datetime import datetime
from . import ProtectedResource
from flask import abort, request
from flask_restful import reqparse
from haruba.permissions import has_read, has_write
from haruba.utils import get_group_root, success


def assemble_directory_contents(group, path):
    group_root = get_group_root(group)
    full_path = os.path.join(group_root, path)
    if not os.path.exists(full_path):
        return abort(404, 'Not Found: %s' % request.url)

    if not os.path.isdir(full_path):
        error = "%s is not a folder" % request.url
        return abort(400, error)

    folders = []
    files = []
    for item in scandir(full_path):
        mod_date = datetime.fromtimestamp(item.stat().st_mtime)
        file_dict = {'name': item.name,
                     'is_file': item.is_file(),
                     'is_dir': item.is_dir(),
                     'size': item.stat().st_size,
                     'modif_date': mod_date.strftime('%Y-%m-%d %H:%M:%S')}
        if item.is_dir():
            file_dict['extension'] = "folder"
            folders.append(file_dict)
        else:
            file_dict['extension'] = item.name.split(".")[-1]
            files.append(file_dict)
    return folders + files


def delete_file_or_folder(file_or_folder):
    try:
        if os.path.exists(file_or_folder):
            if os.path.isfile(file_or_folder):
                os.remove(file_or_folder)
            else:
                shutil.rmtree(file_or_folder)
        else:
            return False
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
        if os.path.exists(new_path):
            abort(400, "%s already exists." % request.url)
        else:
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
