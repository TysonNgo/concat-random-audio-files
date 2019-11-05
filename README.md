# How to use

Modify the `config.json` values.

```js
{
    "ffmpeg_path": "path/to/ffmpeg",
    "ffprobe_path": "path/to/ffprobe",
    "out_dir": "", // the directory the random audio files will be saved to
    "in_dir": "", // the directory (and all sub directories in said directory) to get the random audio files from
    "length_in_seconds": 600, // length of the concatenated file
    "number_of_random_files": 10, // number of files that will be saved to out_dir
    "number_of_concurrent_ffmpeg_processes": 5, // maximum number of ffmpeg processes that will run concurrently
    "intro": "path/to/audio/file.mp3", // audio file to play at the start
    "extension": "mp3"
}
```

Run the python script

```
python3 main.py
```
