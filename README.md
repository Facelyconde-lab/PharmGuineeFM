# PharmaSila Guinée

Plateforme numérique pour l'accès aux médicaments en Guinée. PharmaSila aide les patients à trouver rapidement un médicament disponible dans une pharmacie proche, à un prix affiché en toute transparence, sans avoir à démarcher plusieurs officines.

Site en ligne (démo pilote) : https://facelyconde.pythonanywhere.com

## Le problème

En Guinée, trouver un médicament peut prendre des heures : les stocks réels ne sont pas connus à l'avance, les prix varient sans repère clair d'une pharmacie à l'autre, et certaines officines non accréditées vendent des médicaments contrefaits. PharmaSila centralise ces informations pour gagner du temps aux patients, apporter de la transparence sur les prix, et donner au ministère de la Santé une vue d'ensemble sur les pénuries.

## Fonctionnalités

**Patients** : recherche de médicament avec géolocalisation, comparaison des pharmacies les plus proches avec stock et prix, création de compte, réservation en ligne.

**Pharmacies** : tableau de bord dédié pour mettre à jour les stocks et les prix, ajouter des médicaments au catalogue, traiter les commandes reçues (validation, préparation avec scellé de sécurité, livraison), alertes automatiques de rupture ou de stock faible.

**Ministère de la Santé** : tableau de bord statistique — pénuries par médicament, tendances par quartier de Conakry, médicaments critiques, volumes de commandes.

## Stack technique

Django 5.2 (LTS), Django REST Framework, SQLite, geopy pour le calcul de distance, Python 3.13. Interface web responsive en HTML/CSS/JavaScript (sans framework front-end).

## Installation en local

```bash
git clone https://github.com/Facelyconde-lab/PharmGuineeFM.git
cd PharmGuineeFM
pip install -r requirements.txt
cp .env.example .env
# Modifier .env : générer une SECRET_KEY, ajuster ALLOWED_HOSTS si besoin
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Le site est alors accessible sur `http://127.0.0.1:8000/`, l'administration sur `http://127.0.0.1:8000/admin/`.

## Structure du projet

- `patients/` — comptes et authentification des patients
- `pharmacies/` — pharmacies, stocks, recherche, tableau de bord de gestion
- `medicaments/` — catalogue national des médicaments
- `commandes/` — réservations et suivi de livraison
- `ministere/` — tableau de bord statistique pour le ministère de la Santé

---

Projet pilote, Conakry 2026.
