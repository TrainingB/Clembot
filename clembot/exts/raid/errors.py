from discord.ext.commands import CommandError

class RSVPNotEnabled(CommandError):
    'Exception for RSVP commands in non RSVP channel.'
    pass


class NotARaidChannel(CommandError):
    'Exception for RSVP commands in non RSVP channel.'
    pass


class NotARaidReportChannel(CommandError):
    'Exception for RSVP commands in non RSVP channel.'
    pass