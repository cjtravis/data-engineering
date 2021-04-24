-- Apache Airflow DB
--DROP DATABASE IF EXISTS airflow;
--CREATE DATABASE airflow_db;

--CREATE USER airflow_user with password 'airflow';
--GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- KCMO Open Data DB
--DROP DATABASE IF EXISTS kcmo;
CREATE DATABASE kcmo;

CREATE USER data_user WITH PASSWORD 'data_user';
GRANT ALL PRIVILEGES ON DATABASE kcmo TO data_user;

-- Apache Superset
CREATE USER superset_user WITH PASSWORD 'superset_user';

GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO superset_user;
--create extension postgis;

\c kcmo
CREATE TABLE crime_2021_raw (
    ID SERIAL NOT NULL PRIMARY KEY,
    INFO JSON NULL,
    DATE_ADDED TIMESTAMPTZ,
    WINDOW_START TIMESTAMP,
    WINDOW_END TIMESTAMP
);

-- Insert initialization record
INSERT INTO crime_2021_raw (DATE_ADDED, WINDOW_START, WINDOW_END)
VALUES(
        NOW(),
        to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone,
        to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone
    );