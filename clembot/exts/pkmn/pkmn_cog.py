

class Pokemon():

    def __init__(self, bot, pkmnId, form=None, gender=None, shiny=False, ivAtk=None, ivDef=None,
                 ivSta=None, lvl=None, cp=None, quickMoveId=None, chargeMoveId=None, chargeMove2Id=None):

        self.bot = bot
        self.id = pkmnId
        self.gender = gender
        self.shiny = shiny
        self.lvl = lvl
        self.cp = cp
        self.quickMoveId = quickMoveId
        self.chargeMoveId = chargeMoveId
        self.chargeMove2Id = chargeMove2Id
        self.ivAtk = ivAtk
        self.ivDef = ivDef
        self.ivSta = ivSta
        self.form = form

    @property
    def to_dict(self):
        return {
            'id': self.id,
            'form': self.form,
            'gender': self.gender,
            'shiny': self.shiny,
            'ivAtk': self.ivAtk,
            'ivDef': self.ivDef,
            'ivSta': self.ivSta,
            'lvl': self.lvl,
            'cp': self.cp,
            'quickMoveid': self.quickMoveid,
            'chargeMoveid': self.chargeMoveid,
            'chargeMove2id': self.chargeMove2id
        }


    @classmethod
    def from_dict(cls, bot, data):
        pkmn_id = data['id']
        form = data['form']
        gender = data['gender']
        shiny = data['shiny']
        ivAtk = data['ivAtk']
        ivDef = data['ivDef']
        ivSta = data['ivSta']
        lvl = data['lvl']
        cp = data['cp']
        quickMoveid = data['quickMoveid']
        chargeMoveid = data['chargeMoveid']
        chargeMove2id = data['chargeMove2id']
        return cls(bot, pkmn_id, form=form, gender=gender,
            shiny=shiny, attiv=attiv, defiv=defiv, staiv=staiv,
            lvl=lvl, cp=cp, quickMoveid=quickMoveid,
            chargeMoveid=chargeMoveid, chargeMove2id=chargeMove2id)

    def get_weaknesses(self, number):
        # # Get the Pokemon's number
        # number = pkmn_info['pokemon_list'].index(species)
        # Look up its type
        pk_type = type_list[number]

        # Calculate sum of its weaknesses
        # and resistances.
        # -2 == immune
        # -1 == NVE
        #  0 == neutral
        #  1 == SE
        #  2 == double SE
        type_eff = {}
        for type in pk_type:
            for atk_type in self.bot.type_chart[type]:
                if atk_type not in type_eff:
                    type_eff[atk_type] = 0
                type_eff[atk_type] += type_chart[type][atk_type]

        # Summarize into a list of weaknesses,
        # sorting double weaknesses to the front and marking them with 'x2'.
        ret = []
        for type, effectiveness in sorted(type_eff.items(), key=lambda x: x[1], reverse=True):
            if effectiveness == 1:
                ret.append(type.lower())
            elif effectiveness == 2:
                ret.append(type.lower() + "x2")

        return ret
