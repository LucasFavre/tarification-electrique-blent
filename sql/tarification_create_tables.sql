CREATE TABLE conso_communes_annees (
  code_commune INT NOT NULL,
  nom_commune VARCHAR (50) NOT NULL,
  annee INT NOT NULL,
  conso_moyenne_kwh FLOAT NOT NULL
);


CREATE TABLE conso_moyenne_30jours (
	code_insee_region INT NOT NULL,
	consommation_moyenne_kwh FLOAT NOT NULL
);