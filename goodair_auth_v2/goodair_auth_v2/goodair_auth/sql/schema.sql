
---Tables de dimenssions
CREATE TABLE localisation (
    id_loc SERIAL PRIMARY KEY,
    nom_ville VARCHAR(50),
    pays VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8)
);

CREATE TABLE temps (
    id_temps SERIAL PRIMARY KEY,
    date_ DATE,
    heure INT,
    jour INT,
    mois INT,
    annee INT,
    timestamp_utc TIMESTAMP
);

CREATE TABLE source (
    id_source SERIAL PRIMARY KEY,
    nom_source VARCHAR(50),
    type_source VARCHAR(50)
);
---Tables de Faits
CREATE TABLE mesure_qualite_air (
    id_mesure_air SERIAL PRIMARY KEY,
    aqi DECIMAL(15,2),
    pm25 DECIMAL(5,2),
    pm10 DECIMAL(5,2),
    o3 DECIMAL(5,2),
    no2 DECIMAL(15,2),
    id_source INT NOT NULL,
    id_loc INT NOT NULL,
    id_temps INT NOT NULL,
    CONSTRAINT fk_air_source FOREIGN KEY (id_source) REFERENCES source(id_source),
    CONSTRAINT fk_air_loc FOREIGN KEY (id_loc) REFERENCES localisation(id_loc),
    CONSTRAINT fk_air_temps FOREIGN KEY (id_temps) REFERENCES temps(id_temps)
);

CREATE TABLE mesure_meteo (
    id_mesure_meteo SERIAL PRIMARY KEY,
    temperature DECIMAL(5,2),
    humidite DECIMAL(15,2),
    pression DECIMAL(15,2),
    vitesse_vent DECIMAL(4,2),
    precipitation DECIMAL(15,2),
    indice_uv DECIMAL(3,2),
    id_source INT NOT NULL,
    id_loc INT NOT NULL,
    id_temps INT NOT NULL,
    CONSTRAINT fk_meteo_source FOREIGN KEY (id_source) REFERENCES source(id_source),
    CONSTRAINT fk_meteo_loc FOREIGN KEY (id_loc) REFERENCES localisation(id_loc),
    CONSTRAINT fk_meteo_temps FOREIGN KEY (id_temps) REFERENCES temps(id_temps)
);

--TEST
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

--TEST

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';

INSERT INTO source (nom_source, type_source)
VALUES 
('AQICN', 'Qualite_air'),
('OpenWeatherMap', 'Meteo');




