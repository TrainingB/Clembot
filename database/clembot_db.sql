
create table server_channel_city ( 
	id integer primary key, 
	server_id integer, 
	channel_id integer, 
	city_state text 
);

.mode csv
.separator "|"
.import NEW_GYM_DATA.csv
.import FILE TABLE
.import NEW_GYM_DATA.csv gym_master

UPDATE gym_master 
set JSON = '{' ||
 ' "region_code_key":"' ||region_code_key || '",' ||
 ' "city_state_key":"' ||city_state_key || '",' ||
 ' "gym_code_key":"' ||gym_code_key || '",' ||
 ' "original_gym_name":"' ||original_gym_name || '",' ||
 ' "gym_name":"' ||gym_name || '",' ||
 ' "latitude":"' ||latitude || '",' ||
 ' "longitude":"' ||longitude || '",' ||
 ' "gym_location_city":"' ||gym_location_city || '",' ||
 ' "gym_location_state":"' ||gym_location_state || '",' ||
 ' "gmap_url":"' ||gmap_url || '",' ||
 ' "gym_image":"' ||gym_image || '"}'  
 ;