import datetime
from flask_sqlalchemy import SQLAlchemy
from random import randint

db = SQLAlchemy()


class BaseModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=datetime.datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()
        db.app.logger.info('created new {}'.format(obj))
        return obj


class Rack(BaseModel):
    slots = db.Column(db.SmallInteger)

    def add_server(self):
        assigned_servers = self.servers.count()

        if assigned_servers >= self.slots:
            raise

        self.updated_at = datetime.datetime.now()
        db.session.commit()

        server = Server.create(rack=self)
        db.app.logger('New {} added to {}'.format(server, self))
        return server


class Server(BaseModel):
    STATUS_UNPAID = 'unpaid'
    STATUS_PAID = 'paid'
    STATUS_ACTIVE = 'active'
    STATUS_DELETED = 'deleted'

    status = db.Column(db.String, default=STATUS_UNPAID)
    rack_id = db.Column(db.Integer, db.ForeignKey('rack.id'), nullable=False)
    rack = db.relationship('Rack', backref=db.backref('servers', lazy='dynamic'))

    paid_until = db.Column(db.DateTime, nullable=True)

    def pay(self, until: datetime.datetime):
        if not self.status == 'unpaid':
            raise

        if until <= datetime.datetime.now():
            raise

        self.status = self.STATUS_PAID
        self.paid_until = until
        self.updated_at = datetime.datetime.now()

        db.session.commit()
        db.app.logger('{} was paid'.format(self))

    def delete(self):
        self.status = self.STATUS_DELETED
        self.updated_at = datetime.datetime.now()

        db.session.commit()
        db.app.logger('{} was deleted'.format(self))

    def update_status(self):
        current_time = datetime.datetime.now()

        if self.status == self.STATUS_ACTIVE and self.paid_until >= current_time:
            self.status = self.STATUS_UNPAID
            self.updated_at = current_time
            return

        if self.status == self.STATUS_PAID and (
                current_time >= self.updated_at + datetime.timedelta(seconds=randint(5, 15))
        ):
            self.status = self.STATUS_ACTIVE
            self.updated_at = datetime.datetime.now()
            return
