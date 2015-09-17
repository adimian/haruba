from flask_restful import reqparse
from collections import defaultdict
from flask import current_app, abort
from haruba.endpoints import ProtectedResource
from haruba.utils import success, prep_json, get_sigil_client
from haruba.permissions import has_admin_read, has_admin_write, ZONE_CONTEXT


class Permissions(ProtectedResource):
    @has_admin_read
    def get(self):
        client = get_sigil_client()
        app_name = current_app.config['SIGIL_APP_NAME']
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
            if not isinstance(perm, dict):
                abort(400, "A need item must be a dictionary")
            username = perm.get('username')
            needs = perm.get('needs')
            if not username and not needs:
                msg = "A need item must have a 'username' and 'needs' key"
                abort(400, msg)
            func = getattr(client, func_name)
            func(context=app_name, needs=needs, username=username)
        return success("Success")
