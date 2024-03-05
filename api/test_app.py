import unittest
from tarification_blent_api import app, get_alpha, get_m


class TestApp(unittest.TestCase):
	def setUp(self):
		self.app = app.test_client()


	def test_without_code_commune(self):
		response = self.app.get('/tarification-electrique?code_region=11')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data, b'{"error":"Missing fields."}\n')

	def test_without_code_region(self):
		response = self.app.get('/tarification-electrique?code_commune=77081')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data, b'{"error":"Missing fields."}\n')

	def test_incorrect_code_commune(self):
		response = self.app.get('/tarification-electrique?code_commune=01&code_region=11')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data, b'{"error":"Code commune incorrect."}\n')

	def test_incorrect_code_region(self):
		response = self.app.get('/tarification-electrique?code_commune=77081&code_region=2000')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data, b'{"error":"Code region incorrect."}\n')

	def test_only_codes(self):
		response = self.app.get('/tarification-electrique?code_commune=77081&code_region=11')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, b'{"Estimation du tarif mensuel":6.0}\n')

	def test_all_arguments(self):
		response = self.app.get('/tarification-electrique?code_commune=77081&code_region=11&chauffage=Yes&surface=80&eau_chaude=Yes&nb_pers=3&cuisson=Yes&electromenager_eclairage=Yes')
		self.assertEqual(response.status_code, 200)


	def test_get_alpha(self):
		rows = [[77081,	'Champdeuil', 2022,	7.885], [77081,	'Champdeuil', 2021,	6.237]]
		alpha = get_alpha(rows)
		self.assertEqual(alpha, 1.264)

	def test_get_alpha_oneyear(self):
		rows = [[77081,	'Champdeuil', 2022,	7.885]]
		alpha = get_alpha(rows)
		self.assertEqual(alpha, 1)

	def test_get_alpha_min(self):
		rows = [[77081,	'Champdeuil', 2022,	7.885], [77081,	'Champdeuil', 2022,	8.235]]
		alpha = get_alpha(rows)
		self.assertEqual(alpha, 1)

	def test_get_alpha_max(self):
		rows = [[77081,	'Champdeuil', 2022,	7.885], [77081,	'Champdeuil', 2022,	4.237]]
		alpha = get_alpha(rows)
		self.assertEqual(alpha, 1.3)


	def test_get_m(self):
		row = [11, 7500]
		m = get_m(row)
		self.assertEqual(m, 0.019)

	def test_get_m_max(self):
		row = [11, 25000]
		m = get_m(row)
		self.assertEqual(m, 0.05)


if __name__ == '__main__':
	unittest.main()
