from flask_multipass import IdentityProvider
from .models import SuperSU, User

class UserProvider(IdentityProvider):
    def identify(self, email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            return user
        return None

class SuperSUProvider(IdentityProvider):
    def identify(self, username, password):
        supersu = SuperSU.query.filter_by(username=username).first()
        if supersu and supersu.password == password:
            return supersu
        return None