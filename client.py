import json

import requests

# for debugging purpose
# import http
# http.client.HTTPConnection.debuglevel = 1


class ApiError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code


class Requester(object):
    _s = {}

    @property
    def s(self):
        return self._s['session']

    @property
    def base(self):
        return self._s['url']

    def to(self, piece):
        return ''.join((self.base, piece))

    def request(self, method, piece, **kwargs):
        if kwargs.get('json'):
            del kwargs['json']
            kwargs['data'] = json.dumps(kwargs['data'])
            kwargs.setdefault('headers', {}).update({'Content-Type':
                                                     'application/json'})

        r = self.s.request(method, self.to(piece), **kwargs)
        if r.status_code == 200:
            return r
        else:
            raise ApiError(r.json(), r.status_code)


class Zone(Requester):
    def __init__(self, identifier, name, path):
        self.id = identifier
        self.name = name
        self.path = path

    def update(self, name=None, path=None):
        pass

    def __repr__(self):
        return '<Zone object id:{} name:{} path:/{}>'.format(self.id,
                                                             self.name,
                                                             self.path)

    def new_folder(self, name):
        url = "/files/{}/{}".format(self.name, name)
        self.request('post', url)

    def __getitem__(self, name):
        pass


class Folder(Requester):
    def __init__(self, zone, name, path):
        self.zone = zone
        self.name = name
        self.path = path

    def download_as_zip(self):
        pass

    def rename(self):
        pass

    def delete(self):
        pass

    def __getitem__(self, name):
        pass


class HarubaClient(Requester):
    def __init__(self, url, login=None, password=None, api_key=None):
        self._s['url'] = url
        self._s['session'] = requests.Session()

        if (not login or not password) and not api_key:
            raise ValueError('no authentication method provided')
        self._login(login, password, api_key)

    def _login(self, login, password, api_key):
        r = self.request('post', '/login', data={'login': login,
                                                 'password': password,
                                                 'api_key': api_key})
        assert r.cookies['session']

    @property
    def zones(self):
        r = self.request('get', '/zone')
        return dict([x['name'], Zone(x['id'],
                                     x['name'],
                                     x['path'])] for x in r.json())

    def create_zone(self, name, path):
        payload = {'zones': [{'zone': name, 'path': path}]}
        self.request('post', '/zone', data=payload, json=True)

    def __getitem__(self, name):
        return self.zones[name]

if __name__ == '__main__':
    c = HarubaClient(url='http://localhost:5000',
                     login='eric', password='secret')
    if 'dropbox' not in c.zones:
        c.create_zone('dropbox', '/dropbox')
    dropbox = c['dropbox']
    dropbox.new_folder('eric')
    f = dropbox['eric']
