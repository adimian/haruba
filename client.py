import os
from tempfile import mkstemp
from io import IOBase

import requests
from sigil_client import SigilClient


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
        raise NotImplementedError()

    def __repr__(self):
        return '<Zone object id:{} name:{} path:/{}>'.format(self.id,
                                                             self.name,
                                                             self.path)

    def new_folder(self, name, quiet=False):
        url = "/files/{}/{}".format(self.name, name)
        try:
            self.request('post', url)
        except ApiError as err:
            if err.status_code != 400 or not quiet:
                raise

    def __getitem__(self, name):
        return Folder(zone=self, name=name)


class Transferrable(object):

    def _upload(self, files):
        for fileobj in files:
            if isinstance(fileobj, str):
                fileobj = open(fileobj, 'rb')
            self.request('post', '/upload/{}'.format(self.path),
                         files={'files': fileobj})

    def _download(self):
        r = self.request('get', '/download/{}'.format(self.path))
        return r.content

    def download(self):
        return self._download()


class Folder(Requester, Transferrable):
    def __init__(self, zone, name):
        self.zone = zone
        self.name = name

    @property
    def path(self):
        return '/'.join((self.zone.path, self.name))

    def __repr__(self):
        return '<Folder object name:{} path:/{}>'.format(self.name,
                                                         self.path)

    def list(self):
        r = self.request('get', '/files/{}'.format(self.path))
        return r.json()

    def upload(self, content):
        if not isinstance(content, (list, tuple)):
            content = [content]
        self._upload(content)

    def rename(self):
        raise NotImplementedError()

    def delete(self):
        self.request('delete', '/files/{}'.format(self.path))

    def __getitem__(self, name):
        return File(folder=self, name=name)


class File(Requester, Transferrable):
    def __init__(self, folder, name):
        self.folder = folder
        self.name = name

    @property
    def path(self):
        return '/'.join((self.folder.path, self.name))

    def __repr__(self):
        return '<File object name:{} path:/{}>'.format(self.name,
                                                       self.path)


class HarubaClient(Requester):
    def __init__(self, url, login=None, password=None,
                 api_key=None, proxies=None):
        self._s['url'] = url
        self._s['session'] = requests.Session()
        if proxies:
            self._s['session'].proxies = proxies

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
        self.request('post', '/zone', json=payload)

    def __getitem__(self, name):
        return self.zones[name]

if __name__ == '__main__':
    s = SigilClient(url='http://docker.dev/sigil-api',
                    username='eric', password='secret')
    s.new_app('haruba', quiet=True)

    s.grant('haruba', needs=[['zone', 'read'],
                             ['zone', 'write'],
                             ['permissions', 'read'],
                             ['permissions', 'write']])

    c = HarubaClient(url='http://localhost:5000',
                     login='eric', password='secret')
    if 'dropbox' not in c.zones:
        c.create_zone('dropbox', '/dropbox')
        s.grant('haruba', needs=(('zone', 'read', 'dropbox'),
                                 ('zone', 'write', 'dropbox'),))
    dropbox = c['dropbox']
    dropbox.new_folder('eric', quiet=True)
    folder = dropbox['eric']
    fd, tmp_file = mkstemp(suffix='.txt', prefix='haruba_test_')
    os.close(fd)
    with open(tmp_file, 'w') as f:
        f.write('hello world')
    folder.upload(tmp_file)
    some_file_info = folder.list()[-1]
    that_file = folder[some_file_info['name']]
    content = that_file.download()
    print(content)
