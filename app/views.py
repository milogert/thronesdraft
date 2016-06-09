#!/usr/bin/env python

from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

import requests
import re

from app import app, db, socketio, models, cache

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generic/')
def generic(data):
    return render_template('generic.html', data=data)

@app.route('/room/<uuid>/<room>/')
def pick_room(uuid, room):
    roompacks = models.RoomPack.query.filter(models.RoomPack.room_uuid == uuid).all()
    cards = []
    for roompack in roompacks:
        pack = cache.get_cards(pack_code=roompack.pack_code)
        for card in pack:
            cards.append(card) 

    return render_template('room.html', uuid=uuid, room=room, cards=cards)

@app.route('/staging/<uuid>/<room>/')
def staging(uuid, room):
    '''Staging for users to join the draft pod.'''

    tduser = ''
    if 'thronesdraftuser' in request.cookies:
        tduser = request.cookies['thronesdraftuser']

    try:
        new_room_user = models.RoomPlayer(
            room_uuid=uuid,
            player_name=tduser
        )
        db.session.add(new_room_user)
        db.session.commit()
    except:
        db.session.rollback()

    currentroom = models.Room.query.filter(models.Room.uuid == uuid).first()

    return render_template('staging.html', room=currentroom)

@socketio.on('staging-connect')
def staging_connect(data):
    print('============================\nstaging connect')
    join_room(data['room'])

    currentusers = models.RoomPlayer.query.filter(
        models.RoomPlayer.room_uuid == data['uuid']
    ).all()

    emit('staging-userjoined', {
        'user': data['user'],
        'userList': currentusers,
        'text':  '{user} joined {room}'.format(**data)
    }, broadcast=True, room=data['room'])

@socketio.on('staging-signaldraft')
def staging_signaldraft(data):
    emit('staging-startdraft', broadcast=True, room=data['room'])

@app.route('/create/', methods=['GET', 'POST'])
def create_room():
    if request.method == 'POST':
        room = request.form['roomName']
        players = request.form['playerNumber']
        rounds = request.form['roundNumber']
        packs = request.form.getlist('packs')
        startingPool = request.form['startingPool'].split(r'\r\n')

        # Match the starting pool stuff.
        cardmatch = re.compile('(?P<name>.+)')
        multicardmatch = re.compile('(?P<name>.+) \((?P<code>\d+)\)')
        codematch = re.compile('(?P<code>\d+)')
        for card in startingPool:
            if codematch.match(card):
                pass
            elif multicardmatch.match(card):
                pass
            elif cardmatch.match(card):
                pass
            else:
                continue

        import uuid
        rnd = str(uuid.uuid1())
        new_room = models.Room(
            name=room,
            uuid=rnd,
            players=players,
            staged='0'
        )
        db.session.add(new_room)

        # Put the packs for the room in.
        for pack in packs:
            new_roompack = models.RoomPack(
                room_uuid=rnd,
                pack_code=pack,
            )
            db.session.add(new_roompack)

        try:
            db.session.commit()
        except:
            print('Failed to commit new room.')
            db.session.rollback()

        return redirect('/staging/{}/{}/'.format(rnd, room))

    packs = cache.get_packs()
    return render_template('create.html', packs=packs)

@app.route('/refresh/')
def refresh_data():
    ret = {}

    # Packs
    ret['packs'] = {}
    ret['packs']['old'] = cache.get_packs()
    ret['packs']['new'] = cache.get_packs(recache=True)

    return render_template('recache.html', data=ret)

@socketio.on('chat')
def handle_chat(data):
    emit("chatresponse", data['user'] + ': ' + data['text'], broadcast=True, room=data['room'])

@socketio.on('join')
def on_join(data):
    join_room(data['room'])
    emit("chatresponse", "user joined room", broadcast=True, room=data['room'])

@socketio.on('cardPicked')
def on_card_picked(data):
    # Pick the card here.
    # TODO: find card in database.
    card = cache.get_cards(card_code=data['code'])[0]

    emit('cardSaved', {
        'code': data['code'],
        'name': card.name,
        'octgn_id': card.octgn_id
    })

    remdata = {
        'code': data['code'],
        'text': data['user'] + ' picked card ' + data['code'],
    }
    emit('cardRemoved', remdata, broadcast=True, room=data['room'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)

