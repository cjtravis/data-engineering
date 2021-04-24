CREATE TABLE crime_2021_raw (
    ID SERIAL NOT NULL PRIMARY KEY,
    INFO JSON NULL,
    DATE_ADDED TIMESTAMPTZ,
    WINDOW_START TIMESTAMP,
    WINDOW_END TIMESTAMP
);

INSERT INTO crime_2021_raw (DATE_ADDED, WINDOW_START, WINDOW_END)
VALUES(
        NOW(),
        to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone,
        to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone
    );

DROP  TABLE crime_2021_raw;
SELECT * FROM crime_2021_raw;

SELECT date_trunc('year', now()) --AND CURRENT_TIMESTAMP


select max(to_char(window_end, 'YYYY-MM-DD"T"HH24:MI:ss.ms')) from public.crime_2021_raw;

select to_timestamp(to_char(date_trunc('year', now()), 'YYYY-MM-DD"T"HH24:MI:ss.ms'), 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone