---------------- VERSION 1
create table server_channel_city ( 
	id integer primary key, 
	server_id integer, 
	channel_id integer, 
	city_state text 
);

---------------- VERSION 2
create table guild_channel_configuration ( 
	id integer primary key, 
	guild_id integer, 
	channel_id integer, 
	configuration text 
);

---------------- VERSION 3
.mode csv
.separator "|"
.import NEW_GYM_DATA.csv gym_master

---------------- VERSION 4

create table raid_info (
id integer primary key,
egg_level TEXT,
egg_type TEXT,
egg_img TEXT,
pokemon_list TEXT,
egg_timer INT,
raid_timer INT );


create table guild_user_bingo_card {
id integer primary key,
guild_id integer,
user_id integer,
bingo_card text,
bingo_card_url text,
generated_at text
}