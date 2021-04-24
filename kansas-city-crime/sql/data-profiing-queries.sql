-- ORST_SetSRID(ST_GeomFromGeoJSON(location),4326) geo

-- All data 
with crime as (
    select json_array_elements_text(info)::json as e
    from crime_2021_raw
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
    ,e as payload
    from crime
)
select * 
from event;
--where report_no = 'KC21000615';


CREATE VIEW crime_2021_vw AS
with crime as (
    select json_array_elements_text(info)::json as e
    from crime_2021_raw
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
    ,e as payload
    from crime
)
select * 
from event;

--row_number() over (order by population desc) as country_rank

-- Crimes by patrol
select 
    area as patrol,
    description,
    count(*) as total_occurrences
from public.crime_2021_vw
where description <> ''
group by 
    area,
    description;

create view crime_count_by_patrol_vw AS
select 
    area as patrol,
    description,
    count(*) as total_occurrences
from public.crime_2021_vw
where description <> ''
group by 
    area,
    description;

drop view crime_rank_by_patrol_vw;
create view crime_rank_by_patrol_vw as 
with crimes_by_patrol as (
select * 
from crime_count_by_patrol_vw)
select patrol, description, total_occurrences, row_number() over (partition by patrol order by total_occurrences desc) as crime_rank
from crimes_by_patrol
;

-- Most crime type by patrol ("What crime occurs the least by patrol")
with total as (select patrol, sum(total_occurrences) total_crime_count from crime_rank_by_patrol_vw group by patrol)
select v.patrol, v.description, total_occurrences, t.total_crime_count, round(total_occurrences / t.total_crime_count, 3) * 100 "pct_of_total"
  from crime_rank_by_patrol_vw v 
  join (select patrol, min(crime_rank) highest_rank
          from crime_rank_by_patrol_vw
          group by patrol) l
    on v.patrol = l.patrol 
   and v.crime_rank = l.highest_rank
  join total t on l.patrol = t.patrol

select * from crime_rank_by_patrol_vw
 

with breakdown as (
with total as (select patrol, sum(total_occurrences) total_crime_count from crime_rank_by_patrol_vw group by patrol)
select v.patrol, v.description, total_occurrences, t.total_crime_count, round(total_occurrences / t.total_crime_count, 3) * 100 "pct_of_total"
  from crime_count_by_patrol_vw v 
  join total t on v.patrol = t.patrol
order by 1,2)
select *, floor(sum(pct_of_total) over (partition by patrol order by description))
from breakdown;


select patrol, max(crime_rank) lowest_rank
from crime_rank_by_patrol_vw
group by patrol;