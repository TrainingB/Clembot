#!/usr/bin/python3

import argparse
import os
import subprocess
import sys


#Launcher for clembotv2

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Clembot Launcher - Pokemon Go Bot for Discord")
    parser.add_argument("--no-restart", "-r", help="Disables auto-restart.", action="store_true")
    parser.add_argument("--debug", "-d", help="Enabled debug mode.", action="store_true")
    return parser.parse_known_args()

def run_clembot():
    interpreter = sys.executable
    if interpreter is None:
        raise RuntimeError("Python could not be found")


    launch_args, bot_args = parse_cli_args()
    if launch_args.debug:
        bot_args.append('-d')

    bot_args.append('-l')

    print("Launching...", end=' ', flush=True)


    while True:


        try:
            code = subprocess.call([interpreter, "-m", "clembot", *bot_args])
        except KeyboardInterrupt:
            code = 0
            break
        else:
            if code == 0:
                break
            elif code == 26:
                #standard restart
                if '--fromrestart' not in bot_args:
                    bot_args.append('--fromrestart')
                print("")
                print("Restarting clembot")
                print("")
                continue
            else:
                if launch_args.no_restart:
                    break
                print("")
                print("Restarting clembot from crash")
                print("")

    print("Exit Code: {exit_code}".format(exit_code=code))

args = parse_cli_args()


def main():
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)


    print("Launching clembot...")
    run_clembot()

if __name__ == '__main__':
    main()

