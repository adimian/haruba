import os
from flask import abort
from . import ProtectedResource
from flask_login import current_user
from haruba.database import db, Zone
from flask import current_app, session
from flask_restful import reqparse, inputs
from sqlalchemy.orm.exc import NoResultFound
from haruba.utils import success, prep_json, get_sigil_client
from haruba.permissions import (declare_zone_permissions, has_admin_write,
                                retract_zone_permissions, has_admin_read)


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
                if z.get('zone') and dbzone and dbzone[0] != zone:
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
