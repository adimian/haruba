import requests


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


class Zone(Requester):
    def __init__(self, client, id, name, path):
        self.client = client
        self.id = id
        self.name = name
        self.path = path

    def update(self, name=None, path=None):
        pass


    def new_folder(self, name):
        pass


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
        r = self.s.post(self.to('/login'), data={'login': login,
                                                 'password': password,
                                                 'api_key': api_key})
        assert r.cookies['session']

    def create_zone(self, name, path):
        payload = {'zones': [{'zone': name,
                              'path': path}]}
        self.s.post(self.to('/zone'), data=payload)

    def __getitem__(self, name):
        pass


if __name__ == '__main__':
    c = HarubaClient(url='http://localhost:5000',
                     login='eric', password='secret')
    c.create_zone('dropbox', '/dropbox')
    dropbox = c['dropbox']
    dropbox.new_folder('eric')
    f = dropbox['eric']
