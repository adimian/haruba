import os
from flask import abort
from . import ProtectedResource
from flask_login import current_user
from haruba.database import db, Zone
from flask import current_app, session
from flask_restful import reqparse, inputs
from sqlalchemy.orm.exc import NoResultFound
from haruba.utils import success, prep_json, get_sigil_client, get_group_root
from haruba.permissions import (declare_zone_permissions, has_admin_write,
                                retract_zone_permissions, has_admin_read)
import shutil


class MyZones(ProtectedResource):
    def get(self):
        client = get_sigil_client()
        app_name = current_app.config['SIGIL_APP_NAME']
        session['provides'] = client.provides(context=app_name)['provides']
        zones = []
        for key, values in current_user.zones.items():
            zones.append({"zone": key, "access": values})
        return zones


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
        if not args['zones']:
            abort(400, "No zones found")

        zones = []
        for zone in args["zones"]:
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
            os.makedirs(zone_path, exist_ok=True)
            zones.append(name)
            zone = Zone(name, path)
            db.session.add(zone)
            db.session.commit()
            try:
                declare_zone_permissions(name)
            except Exception as e:
                abort(400, str(e))
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
        parser.add_argument('copy_contents', type=inputs.boolean,
                            default=False)
        parser.add_argument('adopt_if_exists', type=inputs.boolean,
                            default=False)
        args = parser.parse_args()

        zones = []
        for z in args["zones"]:
            keys = ['id', 'name']
            if z.get('zone'):
                z['name'] = z['zone']
            query_filter = {key: z[key] for key in keys if z.get(key)}
            if not query_filter:
                abort(400, "must provide a zone 'id' or a name 'zone' key")
            if not z.get('path'):
                abort(400, "must provide a zone 'path' to update")

            try:
                zone = db.session.query(Zone).filter_by(**query_filter).one()
            except NoResultFound:
                msg = ("Zone with %s does not exist" % query_filter)
                abort(400, msg)

            oldpath = os.path.join(current_app.config['HARUBA_SERVE_ROOT'],
                                   zone.path)
            path = z.get('path')
            if path.startswith("/"):
                path = path[1:]

            dependant = db.session.query(Zone).filter(Zone.path == zone.path,
                                                      Zone.id != zone.id).all()
            zone.path = path

            new_path = os.path.join(current_app.config['HARUBA_SERVE_ROOT'],
                                    path)
            if oldpath != new_path:
                if os.path.exists(new_path):
                    if not args['adopt_if_exists']:
                        abort(400, "This path already exists")
                elif args.copy_contents:
                    try:
                        # if another zone depends on this path, copy folder
                        if dependant:
                            shutil.copytree(oldpath, new_path)
                        # if no zones depend on this path, move folder
                        else:
                            os.makedirs(new_path)
                            shutil.move(oldpath, new_path)
                    except shutil.Error:
                        abort(400, "An error occured moving folder, "
                                   "make sure you are not moving parent "
                                   "folder into child folder")
                else:
                    os.makedirs(new_path)
            db.session.add(zone)
            zones.append(zone.name)
            db.session.commit()
        return success("Successfully updated zones: %s"
                       % ", ".join(zones))
