from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from hashlib import md5

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///api_project.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@app.route('/')
def main():
    return redirect('/admin/')


@app.route('/locations/', methods=['GET'])
def api_locations_list():
    locations = db.session.query(Location)
    locations_dict = []
    for location in locations:
        locations_dict.append(dict(id=location.id, code=location.code, title=location.title))
    return jsonify(locations_dict)


@app.route('/events/', methods=['GET'])
def api_events_list():
    type = request.args.get('type')
    location = request.args.get('location')
    events = db.session.query(Event)
    if type:
        events = events.filter(Event.type == type)
        events_dict = []
        for event in events:
            events_dict.append(
                dict(id=event.id, title=event.title, description=event.description, date=event.date, time=event.time,
                     type=event.type, category=event.category, location=event.location.code, address=event.address,
                     seats=event.seats, participants=event.participants))
        return jsonify(events_dict)
    if location:
        events = db.session.query(Event).join(Location).filter(Location.code == location)
        events_dict = []
        for event in events:
            events_dict.append(
                dict(id=event.id, title=event.title, description=event.description, date=event.date, time=event.time,
                     type=event.type, category=event.category, location=event.location.code, address=event.address,
                     seats=event.seats, participants=event.participants))
        return jsonify(events_dict)
    if type and location:
        events = db.session.query(Event).join(Location).filter(db.and_(Location.code == location, Event.type == type))
        events_dict = []
        for event in events:
            events_dict.append(
                dict(id=event.id, title=event.title, description=event.description, date=event.date, time=event.time,
                     type=event.type, category=event.category, location=event.location.code, address=event.address,
                     seats=event.seats, participants=event.participants))
        return jsonify(events_dict)
    events_dict = []
    for event in events:
        events_dict.append(
            dict(id=event.id, title=event.title, description=event.description, date=event.date, time=event.time,
                 type=event.type, category=event.category, location=event.location.code, address=event.address,
                 seats=event.seats, participants=event.participants))
    return jsonify(events_dict)


@app.route('/enrollments/<int:eventid>', methods=['POST'])
def api_event_post(eventid):
    event = db.session.query(Event).filter(Event.id == eventid).first()
    if len(event.participants) < event.seats:
        enrollment = Enrollment(event_id=eventid)
        db.session.add(enrollment)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})


@app.route('/enrollments/<int:eventid>', methods=['DELETE'])
def api_event_delete(eventid):
    enrollment = db.session.query(Enrollment).filter(Enrollment.event_id == eventid).first()
    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/register/', methods=['POST'])
def api_register():
    name = request.args.get('name')
    email = request.args.get('email')
    password = request.args.get('password')
    location = request.args.get('location')
    picture = request.args.get('picture')
    salt = 'dfgjh6'
    about = request.args.get('about')
    password1 = password + salt
    hash_password = md5(password1.encode()).hexdigest()
    participant_email = db.session.query(Participant).filter(Participant.email == email).first()
    if participant_email:
        return jsonify({"status": "error"})
    if name and email and password and location and about:
        participant = Participant(name=name, email=email, password=hash_password, location=location, about=about)
        db.session.add(participant)
        db.session.commit()
        participant_dict = []
        participant_dict.append(
            dict(id=participant.id, name=participant.name, email=participant.email, password=password,
                 picture=participant.picture,
                 about=participant.about, location=participant.location, enrollments=participant.enrollments))
        return jsonify(participant_dict)
    return jsonify({"status": "error"})


@app.route('/auth/', methods=['POST'])
def api_auth():
    email = request.args.get('email')
    password = request.args.get('password')
    salt = 'dfgjh6'
    password1 = password + salt
    hash_password = md5(password1.encode()).hexdigest()
    participant = db.session.query(Participant).filter(
        db.and_(Participant.email == email, Participant.password == hash_password)).first()
    if participant:
        participant_dict = []
        participant_dict.append(
            dict(id=participant.id, name=participant.name, email=participant.email, picture=participant.picture,
                 about=participant.about, location=participant.location, enrollments=participant.enrollments))
        return jsonify(participant_dict)
    return jsonify({"status": "error"})


@app.route('/profile/<int:uid>', methods=['GET'])
def api_profile(uid):
    participant = db.session.query(Participant).get(uid)
    if participant:
        participant_dict = []
        participant_dict.append(
            dict(id=participant.id, name=participant.name, email=participant.email, picture=participant.picture,
                 about=participant.about, location=participant.location, enrollments=participant.enrollments))
        return jsonify(participant_dict)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    date = db.Column(db.String)
    time = db.Column(db.String)
    type = db.Column(db.String)
    category = db.Column(db.String)
    location_code = db.Column(db.String, db.ForeignKey('locations.code'))
    location = db.relationship('Location', back_populates='events')
    address = db.Column(db.String)
    seats = db.Column(db.Integer)
    participants = db.relationship('Enrollment', back_populates='event')


class Participant(db.Model):
    __tablename__ = 'participants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    picture = db.Column(db.String)
    location = db.Column(db.String)
    about = db.Column(db.String)
    enrollments = db.relationship('Enrollment', back_populates='participant')


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event = db.relationship('Event', back_populates='participants')
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'))
    participant = db.relationship('Participant', back_populates='enrollments')
    datetime = db.Column(db.DateTime, server_default=db.func.now())


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    code = db.Column(db.String)
    events = db.relationship('Event', back_populates='location')


db.create_all()


class EventSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String()
    description = fields.String()
    date = fields.String()
    time = fields.String()
    type = fields.String()
    category = fields.String()
    location = fields.Nested('LocationSchema')
    address = fields.String()
    seats = fields.Integer()
    participants = fields.Nested('EnrollmentSchema', many=True)


class ParticipantSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String()
    email = fields.String()
    password = fields.String()
    picture = fields.String()
    location = fields.String()
    about = fields.String()
    enrollments = fields.Nested('EnrollmentSchema', many=True)


class EnrollmentSchema(Schema):
    id = fields.Integer(dump_only=True)
    event = fields.Nested('EventSchema')
    participant = fields.Nested('ParticipantSchema')
    datetime = fields.DateTime()


class LocationSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String()
    code = fields.String()
    events = fields.Nested('EventSchema', many=True)


event_schema = EventSchema()
participant_schema = ParticipantSchema()
enrollment_schema = EnrollmentSchema()
location_schema = LocationSchema()

db.session.commit()
admin = Admin(app)

admin.add_view(ModelView(Location, db.session))


class EventView(ModelView):
    column_filters = ['date', 'type', 'category', 'location']


admin.add_view(EventView(Event, db.session))


class ParticipantView(ModelView):
    column_searchable_list = ['name', 'email']


admin.add_view(ParticipantView(Participant, db.session))

app.run()
