from pathlib import Path
import json
import os
import random


class NotAnAudioFile(Exception):
    pass

class AssertConfig():
    @staticmethod
    def assertNumber(v):
        assert isinstance(v, float) or \
               isinstance(v, int)

    @staticmethod
    def assertString(s):
        assert isinstance(s, str)

def assertConfig():
    AssertConfig.assertString(config["ffmpeg_path"])
    AssertConfig.assertString(config["ffprobe_path"])
    AssertConfig.assertString(config["out_dir"])
    AssertConfig.assertString(config["out_file_prefix"])
    AssertConfig.assertString(config["in_dir"])
    AssertConfig.assertString(config["extension"])

    AssertConfig.assertNumber(config["duration_in_seconds"])
    AssertConfig.assertNumber(config["number_of_random_files"])

def generate_files():
    ffmpeg = f'"{config["ffmpeg_path"]}" -hide_banner -loglevel panic'
    duration = config['duration_in_seconds']
    files_to_process = config['number_of_random_files']
    out_dir = config['out_dir']
    out_file_prefix = config['out_file_prefix']
    ext = config["extension"]

    files = get_file_list()
    random.shuffle(files)

    for _ in range(files_to_process):
        length = 0
        inputs = []
        while length < duration:
            # TODO fix
            # this could potentially become an infinite loop
            # if the input directory does not contain audio files
            # in any of its sub directories

            if not files:
                files = get_file_list()
            f = files.pop()
            try:
                length += get_duration(f)
                inputs.append(f)
            except NotAnAudioFile as ex:
                print(ex)

        out_file = os.path.join(out_dir,  f'{out_file_prefix}{_}.{ext}')
        for i in range(len(inputs)):
            inputs[i] = f'-i "{inputs[i]}"'
        filters = '-filter_complex ' + \
                  '"' + \
                  ''.join([f'[{i}:a]' for i in range(len(inputs))]) + \
                  f'concat=n={len(inputs)}:v=0:a=1[o],[o]afade=t=out:d=5:st={duration-5} [out]' + \
                  '"'

        # example ffmpeg command
        # "ffmpeg" -hide_banner -loglevel panic \
        # -i "path/to/first/file.mp3" -i "path/to/second/file.mp3" \
        # -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1[o],[o]afade=t=out:d=5:st=595 [out]" \
        # -map [out] -t 600 -y ".\out0.mp3"
        ffmpeg_cmd = f'{ffmpeg} {" ".join(inputs)} {filters} -map [out] -t {duration} -y "{out_file}"'

        # TODO
        # output when ffmpeg subprocesses finish

        print (ffmpeg_cmd)
        os.popen(ffmpeg_cmd)

def get_file_list():
    return list(Path(config['in_dir']).glob('**/*'))

def get_duration(file):
    ffprobe = f'"{config["ffprobe_path"]}"'
    file = f'"{file}"'
    ffprobe_cmd = f'{ffprobe} -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i {file}'
    result = os.popen(ffprobe_cmd).read()
    if not result:
        raise NotAnAudioFile(file)
    return float(result)

with open('config.json') as f:
    config = json.load(f)
    assertConfig()

if __name__ == '__main__':
    generate_files()
