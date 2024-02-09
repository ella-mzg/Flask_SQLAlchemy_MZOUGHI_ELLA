from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import and_
from .database import db
from .models import Client, Chambre, Reservation
from datetime import datetime

main = Blueprint('main', __name__)


# Ajout d'un client et d'une chambre
@main.route('/')
def index():
    chambre_101 = Chambre.query.filter_by(numero=101).first()
    if not chambre_101:
        chambre_101 = Chambre(numero=101, type="Simple", prix=100)
        db.session.add(chambre_101)

    client_martin = Client.query.filter_by(email="martin@example.com").first()
    if not client_martin:
        client_martin = Client(nom="Martin", email="martin@example.com")
        db.session.add(client_martin)
    
    db.session.commit()

    return render_template('index.html')


# Créer une chambre
@main.route('/api/chambres', methods=['POST'])
def ajouter_chambre():
    data = request.get_json()
    numero = data.get('numero')
    type = data.get('type')
    prix = data.get('prix')

    if not numero or not type or not prix:
        return jsonify({'success': False, 'message': 'Paramètres requis manquants.'}), 400

    chambre = Chambre.query.filter_by(numero=numero).first()
    if chambre:
        return jsonify({'success': False, 'message': 'Ce numéro de chambre existe déjà.'}), 400

    new_chambre = Chambre(numero=numero, type=type, prix=prix)
    db.session.add(new_chambre)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Chambre ajoutée avec succès.'}), 201


# Modifier une chambre
@main.route('/api/chambres/<int:id>', methods=['PUT'])
def modifier_chambre(id):
    data = request.get_json()
    
    if 'numero' not in data or 'type' not in data or 'prix' not in data:
        return jsonify({'success': False, 'message': 'Paramètres requis manquants.'}), 400
    
    chambre = Chambre.query.get(id)
    if not chambre:
        return jsonify({'success': False, 'message': 'Chambre introuvable.'}), 404

    numero = data['numero']
    chambre.numero = numero

    type_chambre = data['type']
    chambre.type = type_chambre

    prix = data['prix']
    chambre.prix = prix

    db.session.commit()

    return jsonify({'success': True, 'message': 'Chambre modifiée avec succès.'}), 200


# Supprimer une chambre
@main.route('/api/chambres/<int:id>', methods=['DELETE'])
def supprimer_chambre(id):
    chambre = Chambre.query.get(id)
    if not chambre:
        return jsonify({'success': False, 'message': 'Chambre introuvable.'}), 404

    db.session.delete(chambre)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Chambre supprimée avec succès.'}), 200


# Afficher les chambres disponibles entre deux dates
@main.route('/api/chambres/disponibles', methods=['GET'])
def chambres_disponibles():
    date_arrivee = request.args.get('date_arrivee')
    date_depart = request.args.get('date_depart')

    if not date_arrivee or not date_depart:
        return jsonify({'success': False, 'message': 'Paramètres requis manquants.'}), 400

    date_arrivee = datetime.strptime(date_arrivee, '%Y-%m-%d')
    date_depart = datetime.strptime(date_depart, '%Y-%m-%d')

    conflicting_reservations = Reservation.query.filter(
        and_(Reservation.date_arrivee < date_depart, Reservation.date_depart > date_arrivee)
    ).all()

    conflicting_chambre_ids = [r.id_chambre for r in conflicting_reservations]

    available_chambres = Chambre.query.filter(~Chambre.id.in_(conflicting_chambre_ids)).all()

    available_chambres_json = [
        {
            "id": chambre.id,
            "numero": chambre.numero,
            "type": chambre.type,
            "prix": chambre.prix
        }
        for chambre in available_chambres
    ]

    return jsonify(available_chambres_json), 200


# Ajouter une reservation
@main.route('/api/reservations', methods=['POST'])
def ajouter_reservation():
    data = request.get_json()
    id_client = data.get('id_client')
    id_chambre = data.get('id_chambre')
    date_arrivee = data.get('date_arrivee')
    date_depart = data.get('date_depart')
    statut = data.get('statut')

    if not all([id_client, id_chambre, date_arrivee, statut]):
        return jsonify({'success': False, 'message': 'Paramètres requis manquants.'}), 400

    date_arrivee = datetime.strptime(date_arrivee, '%Y-%m-%d')
    date_depart = datetime.strptime(date_depart, '%Y-%m-%d') if date_depart else None

    nouvelle_reservation = Reservation(id_client=id_client, id_chambre=id_chambre, date_arrivee=date_arrivee, date_depart=date_depart, statut=statut)
    db.session.add(nouvelle_reservation)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Réservation créée avec succès.'}), 201


# Annuler une réservation
@main.route('/api/reservations/<int:id>', methods=['DELETE'])
def supprimer_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is None:
        return jsonify({'success': False, 'message': 'Réservation introuvable.'}), 404

    db.session.delete(reservation)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Réservation supprimée avec succès.'}), 200