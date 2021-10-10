# BilibiliDynamicTimeMachine
A small tool to save bilibili dynamic data including all images to local given a specific account.

Originally wrote for HoloCN and make it public after a year because of the story of HecaTia ends.

Usage:
```
BilibiliDynamicTimeMachine.exe [-h] [-n NAME] [-o SAVE_ROOT] uid

positional arguments:
  uid           UID of the account you want to save its dynamics.

optional arguments:
  -h, --help    show this help message and exit.
  -n NAME       The name to use in the local save. If not specified, the username of the bilibili account will be used.
  -o SAVE_ROOT  The root directory of the local save.
```

The program will save all dynamics (including albums, forwards, dynamics, living calendar, short videos (which has been deprecated by Bilibili), and dynamics for articles, videos, and audios) into .jsonl files. Every type has its own .jsonl file. In the .jsonl file, a line represents a record including dynamic id, timestamp and its data. For all images and short videos, the program will save them to the local and will add a "pictures_local" in the .jsonl file after the "pictures" key-value.
