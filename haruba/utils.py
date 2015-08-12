class User(object):

    def __init__(self, login, provides):
        self.login = login
        self.roles = []
        print(provides)
        for group in provides.get('groups', []):
            self.roles.append(group)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.login
