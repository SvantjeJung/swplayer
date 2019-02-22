#!/usr/bin/env python3

"""
Sleep-Well Player.

This script allows to play multiple media files before automatically shutting system down.
This is especially useful when falling asleep during media playback.

Allows to set media files that are played and directories that are used to choose randomly media files from.
In order to prevent playing recently played files a logfile is saved in '~/.swplayer/playlist.log'.
This logfile can be used to prevent that the last *n* logged files are chosen for playback.

Shutdown can be initiated by reaching end of playlist or timeout.

:version 0.1.0 - 2019-02-20

"""

import argparse
import datetime
import logging
import os
import pathlib
import random
import subprocess


def parse_arguments():
    """
    Parsing command line arguments
    :return: arguments
    """
    app = argparse.ArgumentParser()
    app.add_argument('--files', '-f',
                     dest='files',
                     nargs='*',
                     default='.',
                     help="Files and folders to use for playback.")
    app.add_argument('--delete', '-d',
                     dest='delete',
                     action='store_true',
                     help="Delete current playlist history.")
    app.add_argument('--formats',
                     dest='formats',
                     nargs='*',
                     default=['mp3', 'mp4', 'm4a', 'flac', 'webm'],
                     help="Accepted file formats.")
    app.add_argument('--hist_max', '-hmax',
                     dest='hist_max',
                     default=100,
                     type=int,
                     help="Prevents program to choose recently played titles from playlist history.")
    app.add_argument('--max_titles', '-n',
                     dest='max_titles',
                     default=1,
                     type=int,
                     help="Number of titles to be played.")
    app.add_argument('--timelimit', '-t',
                     dest='tlim',
                     default=180,
                     type=float,
                     help="Timelimit in minutes.")
    app.add_argument('--player', '-p',
                     dest='player',
                     default='mplayer',
                     help="Sets mediaplayer to use. Tested with mplayer. To test with vlc, ffmpeg.")
    app.add_argument('--rain',
                     dest='rain',
                     action='store_true',
                     help="Play sound of rain, if playlist empty and as long as timeout not reached.")
    app.add_argument('--verbose', '-v',
                     dest='verbose',
                     action='store_true',
                     help="Show debug messages")
    args = app.parse_args()
    return args


def get_last_n_played_titles_from_history(logfile, n):
    """
    Get last n played titles from logfile.
    :param logfile: Should be ~/.swplayer/playlist.log
    :param n: number of titles to take from history
    :return: list of n titles
    """
    history = list()
    cat = subprocess.Popen(["cat", logfile], stdout=subprocess.PIPE)
    grep = subprocess.Popen(["grep", "PLAYED"], stdin=cat.stdout, stdout=subprocess.PIPE)
    tail = subprocess.run(["tail", "-n", str(n)], stdin=grep.stdout, stdout=subprocess.PIPE, check=True)

    for t in tail.stdout.decode().split("\n"):
        if len(t) == 0:
            continue

        history.append(pathlib.Path(t.split("PLAYED")[1].strip()))

    return history


def get_random_titles(dirs, num_random_titles, formats, history):
    """
    Get n random titles from directories.
    :param dirs: list of directories
    :param num_random_titles: number of random titles to choose
    :return: playlist
    """
    audio_in_dirs = list()

    if len(dirs) == 0:
        dirs.append(str(pathlib.Path.cwd()))

    for n in dirs:
        # get mp3 or flac from dirs
        for p in formats:
            audio_in_dirs.extend(pathlib.Path(n).absolute().glob('*.' + p))

        logging.debug("AUDIOS (%d): %s", len(audio_in_dirs), audio_in_dirs)

    # try to only use those files which are not in recent playlist history
    tmp = list(set(audio_in_dirs) - set(history))

    logging.debug("DIFFERENCE (%d): %s", len(tmp), tmp)

    if tmp:
        audio_in_dirs = tmp
    else:
        logging.warning("All available media in %s was recently played. Randomly choosing from all available media.", dirs)


    playlist = list()

    if audio_in_dirs:
        # media files found
        for i in range(0, num_random_titles):
            playlist.append(random.choice(audio_in_dirs))

    return playlist


def main():
    # =============================================================================================
    # initialize

    args = parse_arguments()

    swplayer = pathlib.Path("/home", os.getenv("USER"), ".swplayer")
    swplayer.mkdir(parents=True, exist_ok=True)

    logfile = swplayer.joinpath(pathlib.Path("playlist.log"))

    print(logfile)

    if args.delete:
        filemode = 'w'
    else:
        filemode = 'a'

    logging.basicConfig(filename=logfile, filemode=filemode, format='%(levelname)s:%(asctime)s => %(message)s',
                        level=logging.INFO)

    if args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.debug("*** %s", args)

    # =============================================================================================
    files = list()
    dirs = list()

    # sort by files and folders
    for f in args.files:
        if pathlib.Path(f).is_file():
            files.append(f)
        elif pathlib.Path(f).is_dir():
            dirs.append(f)
        else:
            logging.warning("Neither file nor directory")

    # =============================================================================================
    # history
    history = get_last_n_played_titles_from_history(logfile, args.hist_max)
    logging.debug("HISTORY (%d): %s\n", len(history), history)

    # =============================================================================================
    playlist = list()

    # put all files in playlist
    for n in files:
        if len(playlist) < args.max_titles:
            playlist.append(n)
            continue
        break

    # get audiofiles from directories, if more files needed for playback
    num_random_titles = args.max_titles - len(playlist)
    if num_random_titles > 0:
        playlist = get_random_titles(dirs, num_random_titles, args.formats, history)

    if not playlist and not args.rain:
        print("\nNo media for playback found in", dirs, "\nAborting.\n")
        logging.debug("No media for playback in : %s", dirs)
        return

    logging.debug("PLAYLIST (%d): %s", len(playlist), playlist)

    # play files
    time_to_play = args.tlim * 60
    for p in playlist:
        start = datetime.datetime.now()
        try:
            logging.info("PLAYED %s", pathlib.Path(p).absolute())
            subprocess.run([args.player, p], timeout=time_to_play)
        except subprocess.TimeoutExpired:
            logging.info("*** Aborted playing due to timeout.")
            break
        time_to_play -= ((datetime.datetime.now() - start).total_seconds())

    if time_to_play > 0 and args.rain:
        # TODO play rain sounds
        pass

    # =============================================================================================
    # shutdown
    os.system("shutdown -now")


# =============================================================================================
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Cancelled playback with following shutdown.")
