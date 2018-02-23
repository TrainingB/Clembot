
create table server_channel_city ( 
	id integer primary key, 
	server_id integer, 
	channel_id integer, 
	city_state text 
);

create table guild_channel_configuration ( 
	id integer primary key, 
	guild_id integer, 
	channel_id integer, 
	configuration text 
);

.mode csv
.separator "|"
.import NEW_GYM_DATA.csv gym_master


 update gym_master set gym_code_key = word_1 || word_2  where city_state_key = 'BURBANKCA'  ;
 update gym_master set gym_code_key = word_1||word_2||word_3 where gym_code_key IN ('FADO','BUVI','FILU','FOLA','WABR')  and city_state_key='BURBANKCA';
 UPDATE gym_master set JSON = '{' || ' "region_code_key":"' ||region_code_key || '",' ||' "city_state_key":"' ||city_state_key || '",' ||' "gym_code_key":"' ||gym_code_key || '",' ||' "original_gym_name":"' ||original_gym_name || '",' ||' "gym_name":"' ||gym_name || '",' ||' "latitude":"' ||latitude || '",' ||' "longitude":"' ||longitude || '",' ||' "gym_location_city":"' ||gym_location_city || '",' ||' "gym_location_state":"' ||gym_location_state || '",' ||' "gmap_url":"' ||gmap_url || '",' ||' "gym_image":"' ||gym_image || '"}'  ;


 update gym_master set gym_code_key = word_1 || word_2 ||word_3 where rowid=1480  ;
 
 
 