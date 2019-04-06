''' Configuration for Clembot '''

# Rename to config_template.py

bot_token = 'place your bot token here'

default_prefix = '!'
bot_users = {
	"owner" : 0, # discord user id
	"trusted_users" : [0], # other trusted users
}

db_config_details = {
    "password" : 'password',
    "hostname" : 'hostname',
    "username" : 'postgres',
    "database" : "database"
}

api_keys = {
	"google-api-key" : "google-api-key",
	"google-shortner-key" : "google-shortner-key",
}

sqlite_db = "path to clembot-db",

