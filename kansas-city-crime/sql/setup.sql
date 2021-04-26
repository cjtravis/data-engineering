--Apache Airflow DB
DROP DATABASE IF EXISTS airflow;
CREATE DATABASE airflow;
\c airflow
CREATE USER airflow with password 'airflow';
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- KCMO Open Data DB
--DROP DATABASE IF EXISTS kcmo;
--CREATE DATABASE kcmo;

\c pipelines
-- create extension for kcmo database
create extension if not exists postgis;

create schema kcmo;

CREATE TABLE kcmo.crime_2021_raw (
    ID SERIAL NOT NULL PRIMARY KEY,
    INFO JSON NULL,
    DATE_ADDED TIMESTAMPTZ DEFAULT NOW(),
    WINDOW_START TIMESTAMP,
    WINDOW_END TIMESTAMP
);

-- Insert initialization record
INSERT INTO kcmo.crime_2021_raw (DATE_ADDED, WINDOW_START, WINDOW_END)
VALUES(
        NOW(),
        to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone,
        to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone
    );

CREATE USER etl_user WITH PASSWORD 'etl_user';
--GRANT ALL PRIVILEGES ON DATABASE kcmo TO etl_user;
GRANT USAGE ON schema kcmo to etl_user;
GRANT ALL PRIVILEGES ON kcmo.crime_2021_raw to etl_user;
grant usage, select on kcmo.crime_2021_raw_id_seq to etl_user;
--grant insert on crime_2021_raw to etl_user;
--grant all privileges on crime_2021_raw to etl_user;
--grant usage, select on crime_2021_raw_id_seq to etl_user;

-- Apache Superset
CREATE USER superset_user WITH PASSWORD 'superset_user';
GRANT USAGE ON SCHEMA kcmo to superset_user;
GRANT SELECT ON ALL TABLES IN SCHEMA kcmo TO superset_user;
--postgresql://superset_user:superset_user@host.docker.internal:5432/kcmo


-- Create Views for Superset
CREATE VIEW kcmo.crime_2021_vw AS
with crime as (
    select json_array_elements_text(info)::json as e
    from kcmo.crime_2021_raw
),
event as (
    select 
    e->>'report_no'::varchar as report_no
    ,to_timestamp(e->>'report_date', 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone as report_date
    ,e->>'report_time' as report_time
    ,to_timestamp(e->>'from_date', 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone as from_date
    ,e->>'from_time' as from_time
    ,e->>'to_time' as to_time
    ,e->>'offense' as offsense
    ,e->>'ibrs' as ibrs
    ,e->>'description' as description
    ,e->>'beat' as beat
    ,e->>'address' as address
    ,e->>'city' as city
    ,e->>'zip_code' as zip_code
    ,e->>'rep_dist' as rep_dist
    ,e->>'area' as area
    ,e->>'dvflag' as dvflag
    ,e->>'involvement' as involvement
    ,e->>'sex' as sex
    ,e->>'age' as age
    ,e->>'firearmused_flag' as firearmused_flag
    ,e->>'location' as location
    ,ST_X(e ->> 'location') AS lon
	,ST_Y(e ->> 'location') AS lat
    ,e as payload
    from crime
)
select * 
from event;

GRANT SELECT ON kcmo.crime_2021_vw TO superset_user;
GRANT SELECT ON kcmo.crime_2021_vw TO etl_user;

create view kcmo.crime_count_by_patrol_vw AS
select 
    area as patrol,
    description,
    count(*) as total_occurrences
from kcmo.crime_2021_vw
where description <> ''
group by 
    area,
    description;

GRANT SELECT ON kcmo.crime_count_by_patrol_vw TO superset_user;
GRANT SELECT ON kcmo.crime_count_by_patrol_vw TO etl_user;

create view kcmo.crime_rank_by_patrol_vw as 
with crimes_by_patrol as (
select * 
from kcmo.crime_count_by_patrol_vw)
select patrol, description, total_occurrences, row_number() over (partition by patrol order by total_occurrences desc) as crime_rank
from crimes_by_patrol
;

GRANT SELECT ON kcmo.crime_rank_by_patrol_vw TO superset_user;
GRANT SELECT ON kcmo.crime_rank_by_patrol_vw TO etl_user;