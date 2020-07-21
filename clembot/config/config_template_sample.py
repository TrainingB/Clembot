''' Configuration for Clembot '''


bot_token = 'pLaCEyOur.bOTtoKeN.HerE'
default_prefix = '!'
environment = "dev"
preload_extensions = [
	'exts.config',
	'exts.pkmn',
	'exts.gymmanager',
	'exts.gyms',
	'exts.raid',
	# 'exts.autorespond',
	# 'exts.bingo',
	# 'exts.badges',
	# 'exts.draft',
	# 'exts.profile',
	# 'exts.rolebyreaction',
	# 'exts.silph',
	# 'exts.trade',
	# 'exts.spawns',
	# 'exts.leaderboard',
	# 'exts.wild',
	# 'exts.research'
]
bot_users = {
	"owner" : 289657500167438336,
	"trusted_users" : [289657500167438336, 339586795136090114, 310619324958244876],
}

# minimum required permissions for bot user 268822608
bot_permissions = 268823632

db_config_details = {
    "password" : 'pAssWord',
    "hostname" : 'your.database.host.ip',
	"username" : 'useRNaMe',
 	"database" : "name-of-the-database",
	"schema" : "public",
	"port" : 5433,
	"debug" : True
}

api_keys = {
	"google-api-key" : "gOOGle-aPI-KeY"
}




type_emoji = {
	"normal"   : "<:type_normal:394992044784746507>",
	"fire"     : "<:type_fire:394992044310921247>",
	"water"    : "<:type_water:394992044562448394>",
	"electric" : "<:type_electric:394992043669192716>",
	"grass"    : "<:type_grass:394992044462047244>",
	"ice"      : "<:type_ice:394992044554190868>",
	"fighting" : "<:type_fighting:394992044562448385>",
	"poison"   : "<:type_poison:394992044763906048>",
	"ground"   : "<:type_ground:394992044126371841>",
	"flying"   : "<:type_flying:394992043660804097>",
	"psychic"  : "<:type_psychic:394992044478824458>",
	"bug"      : "<:type_bug:394992043551752193>",
	"rock"     : "<:type_rock:394992044478693386>",
	"ghost"    : "<:type_ghost:394992044688539651>",
	"dragon"   : "<:type_dragon:394992043807735808>",
	"dark"     : "<:type_dark:394992043706810368>",
	"steel"    : "<:type_steel:394992044604391434>",
	"fairy"    : "<:type_fairy:394992043312807949>"
}

weather_emoji = {
	"clear"        : "<:weather_clear:419935674662125568>",
	"cloudy"       : "<:weather_cloudy:419935764290469890>",
	"foggy"        : "<:weather_foggy:419936215031087115>",
	"partlycloudy"  : "<:weather_partlycloudy:419935852672843776>",
	"rainy"        : "<:weather_rainy:419936002581463045>",
	"snowy"        : "<:weather_snowy:419936112455188480>",
	"windy"        : "<:weather_windy:419936396556369920>",
	"extreme"      : "<:weather_extreme:419942598061457408>",
	"none"         : "<:weather_none:419944231289880577>"
}


misc_emoji = {
	"add_friend": "<:add_friend:733944456696430662>",
	"remote_raid": "<:remote_raid:733940725129019413>",
	"interested": "<:sign_i:734129673197584494>",
	"here": "<:sign_h:734129727937445948>",
	"coming": "<:sign_c:734128533349072988>",
	"info": "<:icon_info:734670376755527710>",
	"error": "<:icon_error:734670377011249192>",
}

bot_language= "en"
pokemon_language= "en"
egg_timer=10
raid_timer=10

allow_assume = {"EX": "True", "5": "True", "4": "False", "3": "False", "2": "False", "1": "False"}
team_dict= {"mystic": ":mystic:", "valor": "valor", "instinct": ":instinct:"}
omw_id= ":omw:"
here_id= ":here:"

