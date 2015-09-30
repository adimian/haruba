from flask_restful import Resource
from ..utils import login_required
from ..permissions import (has_read, has_write, has_admin_read,
                           has_admin_write)


class ProtectedResource(Resource):
    method_decorators = [login_required]


class ProtectedReadResource(Resource):
    method_decorators = [has_read]


class ProtectedWriteResource(Resource):
    method_decorators = [has_write]


class ProtectedAdminReadResource(Resource):
    method_decorators = [has_admin_read]


class ProtectedAdminWriteResource(Resource):
    method_decorators = [has_admin_write]
