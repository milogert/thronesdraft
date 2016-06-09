#!/usr/bin/env python

import requests

from app import db, models

def get_cards(card_code=None, pack_code=None, recache=False):
    '''
    Used for recaching cards.
    '''

    cards = []
    dbcards = []

    if recache:
        try:
            print('Truncating `Card` table.')
            models.Card.query.delete()
            db.session.commit()
        except:
            print('Something happened to rollback.')
            db.session.rollback()
    else:
        q = models.Card.query
        # If we have a pack code we should filter by it.
        if card_code:
            q = q.filter(models.Card.code == card_code)
        elif pack_code:
            q = q.filter(models.Card.pack_code == pack_code)

        dbcards = q.all()

    if not dbcards or (recache and (card_code or pack_code)):
        res = []
        if card_code:
            res = requests.get('https://thronesdb.com/api/public/card/{}'.format(card_code))
            res = [ res.json() ]
        elif pack_code:
            res = requests.get('https://thronesdb.com/api/public/cards/{}.json'.format(pack_code))
            res = res.json()
        else:
            return []
        
        webcards = res

        for webcard in webcards:
            new_card = models.Card(
                pack_code=webcard['pack_code'],
                pack_name=webcard['pack_name'],
                position=webcard['position'],
                code=webcard['code'],
                name=webcard['name'],
                octgn_id=webcard['octgn_id'],
                url=webcard['url'],
                imagesrc=webcard['imagesrc']
            )
            db.session.add(new_card)
        db.session.commit()
        cards = webcards
    else:
        cards = dbcards

    return cards


def get_packs(recache=False):
    '''Used for caching packs.

    If you set "recache" it will look for the cache but update everything as
    well.
    '''

    packs = []
    dbpacks = []

    # If we are recaching, drop the table.
    if recache:
        try:
            print('Truncating `Pack` table.')
            models.Pack.query.delete()
            db.session.commit()
        except:
            print('Something happened to rollback.')
            db.session.rollback()
    else:
        dbpacks = models.Pack.query.filter(models.Pack.available is not "").order_by(models.Pack.cycle_position.asc()).all()

    # If we didn't find anything or we are intentionally recaching, then we
    # should cache it.
    if not dbpacks or recache:
        res = requests.get('https://thronesdb.com/api/public/packs/')
        
        webpacks = res.json()

        for webpack in webpacks:
            new_pack = models.Pack(
                name=webpack['name'],
                code=webpack['code'],
                position=webpack['position'],
                cycle_position=webpack['cycle_position'],
                available=webpack['available'],
                known=webpack['known'],
                total=webpack['total'],
                url=webpack['url']
            )
            db.session.add(new_pack)
        db.session.commit()
        packs = webpacks
    else:
        '''In the event that our database is being used.'''
        packs = [x.serialize for x in dbpacks]

    # Return the packs, whatever version we have at this point.
    return packs

