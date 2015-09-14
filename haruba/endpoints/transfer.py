import os
from flask_restful import reqparse, inputs
from flask import abort, request, send_file
from werkzeug.datastructures import FileStorage
from haruba.utils import (success, unzip, make_zip, make_selective_zip)
from haruba.endpoints import ProtectedReadResource, ProtectedWriteResource


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

        if not os.path.isfile(filepath):
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
