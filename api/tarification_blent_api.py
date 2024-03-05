from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

def get_db_connection():
	"""
	Crée une connexion psycopg2 à la base de données pour pouvoir exécuter des requêtes.
	"""
    conn = psycopg2.connect(host='35.205.162.105',
                            database='tarification',
                            user='blent',
                            password='blent')
    return conn


def get_alpha(rows):
	"""
	Renvoie le alpha de la formule de tarification électrique.
	Alpha = consommation de 2022/consommation de 2021 pour une commune. La valeur est comprise dans [1,1.3].

	"""
	if len(rows) < 2:
		return 1
	if rows[0][3] > rows[1][3]:
		return round(min(rows[0][3]/rows[1][3], 1.3), 3)
	return round(max(rows[0][3]/rows[1][3], 1),  3)


def get_m(row):
	"""
	Renvoie le M de la formule de tarification électrique.
	M = 0.01 * consommation moyenne des 30 derniers jours / 4000. La valeur doit être inférieure à 0.05.
	"""
	return round(max(0.05, 0.01 * row[1]/4000), 3)

@app.route('/tarification-electrique', methods = ['GET'])
def get_tarification():
	"""
	Renvoie le prix estimé pour un mois selon la formule de la tarification électrique.
	"""
	try:
		if not ({'code_commune', 'code_region'} <= set(request.args.keys())):
			return jsonify({'error': "Missing fields."}), 400

		conn = get_db_connection()
		with conn.cursor() as curs:

			curs.execute('SELECT * FROM conso_communes_annees WHERE code_commune = ' + request.args.get('code_commune') + ';')
			rows_commune = curs.fetchall()

			curs.execute('SELECT * FROM conso_moyenne_30jours WHERE code_insee_region = ' + request.args.get('code_region') + ';')
			rows_region = curs.fetchall()


		if rows_commune == []:
			return jsonify({'error': 'Code commune incorrect.'}), 400
		alpha = get_alpha(rows_commune)

		if rows_region == []:
			return jsonify({'error': 'Code region incorrect.'}), 400
		m = get_m(rows_region[0])

		conso_annuelle = 0

		if request.args.get('chauffage', '') == 'Yes':
			conso_annuelle += 110 * int(request.args.get('surface', 50))

		if request.args.get('eau_chaude', '') == 'Yes':
			conso_annuelle += 800 * int(request.args.get('nb_pers', 2))

		if request.args.get('cuisson', '') == 'Yes':
			conso_annuelle += 200 * int(request.args.get('nb_pers', 2))

		if request.args.get('electromenager_eclairage', '') == 'Yes':
			conso_annuelle += 1100

		estim_mensuelle = (0.1558 + alpha * m) * conso_annuelle/12 + 6

		return jsonify({'Estimation du tarif mensuel' : estim_mensuelle}), 200

	except Exception as e:
		return jsonify({'error': str(e)}), 500