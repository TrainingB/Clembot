"""Create 64bit unique IDs with timestamps embedded."""

import os
import time

# 07 Aug 2017 16:26:00 GMT
CLEM_EPOCH = 1502123160


def to_timestamp(_id):
    _id = _id >> 22   # strip the lower 22 bits
    _id += CLEM_EPOCH    # adjust for meowth epoch
    _id = _id // 1000  # convert from milliseconds to seconds
    return _id


def create():
    """Create and return snowflake for current time."""
    sleep = lambda x: time.sleep(x/1000.0)
    worker_id = 1
    data_center_id = 1
    worker_id_bits = 5
    data_center_id_bits = 5
    max_worker_id = -1 ^ (-1 << worker_id_bits)
    max_data_center_id = -1 ^ (-1 << data_center_id_bits)
    sequence_bits = 12
    worker_id_shift = sequence_bits
    data_center_id_shift = sequence_bits + worker_id_bits
    timestamp_left_shift = sequence_bits + worker_id_bits + data_center_id_bits
    sequence_mask = -1 ^ (-1 << sequence_bits)

    assert worker_id >= 0 and worker_id <= max_worker_id
    assert data_center_id >= 0 and data_center_id <= max_data_center_id

    last_timestamp = -1
    sequence = 0

    while True:
        timestamp = int(time.time()*1000)
        if last_timestamp > timestamp:
            # clock is moving backwards. waiting until last_timestamp
            sleep(last_timestamp-timestamp)
            continue

        if last_timestamp == timestamp:
            sequence = (sequence + 1) & sequence_mask
            if sequence == 0:
                # sequence overrun
                sequence = -1 & sequence_mask
                sleep(1)
                continue
        else:
            sequence = 0

        last_timestamp = timestamp

        yield (
                ((timestamp - CLEM_EPOCH) << timestamp_left_shift) |
                (data_center_id << data_center_id_shift) |
                (worker_id << worker_id_shift) |
                sequence)

class Snowflake:

    def __init__(self):
        self.flake = create()

    def next(self):
        return next(self.flake)


class Base36:
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'


    @classmethod
    def dumps(self, number):
        """Dumps an integer into a base36 string.
        :param number: the 10-based integer.
        :returns: the base36 string.
        """
        if not isinstance(number, int):
            raise TypeError('number must be an integer')

        if number < 0:
            return '-' + Base36.dumps(-number)

        value = ''

        while number != 0:
            number, index = divmod(number, len(Base36.alphabet))
            value = Base36.alphabet[index] + value

        return value or '0'


    @classmethod
    def loads(self, value):
        """Loads a base36 string and parse it into 10-based integer.
        :param value: the base36 string.
        :returns: the parsed integer.
        """
        return int(value, 36)


class CUIDGenerator:


    @classmethod
    def cuid(cls, id):
        try:
            value = Base36.dumps(divmod(id, 10 ** 6)[1])
            return value.upper()

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")
            return id

def main():
    my_snowflake = create()
    for i in range(1, 20):
        print(next(my_snowflake))


if __name__=='__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")


