# Sleep-Well Player
This script allows to play multiple media files before automatically shutting system down.
This is especially useful when falling asleep during media playback.

Allows to set media files to be played and directories that are used to choose randomly media files from.
In order to prevent playing recently played files a logfile is saved in '~/.swplayer/playlist.log'.
This logfile can be used to prevent that the last *n* logged files are chosen for playback.

Shutdown can be initiated by reaching end of playlist or timeout.

**Attention**: shutdown will be executed, all unsaved data, browser sessions or similiar may be lost!

## File Formats and player
Command line argument '--formats' currently defaults to the media file formats: mp3, mp4, m4a, flac, webm.

swplayer was only tested by using 'mplayer' for media playback.
For other players change the argument '--player' to program you like and see if it works. 

## Usage
```
# play 2 random titles from directory
./swplayer.py -f <directory> -n 2

# will play 'foo.mp3' and 1 random title from current directory
./swplayer.py -f foo.mp3 -n 2

# will play 1 random title from directory, but will in any case shutdown computer after 20 minutes (timeout defaults to 180)
./swplayer.py -f <directory> -n 1 -t 20

# will play 1 random title from directory, random title will not match any of the last 20 played files (hmax defaults to 100) 
./swplayer.py -f <directory> -n 1 -hmax 20
```
