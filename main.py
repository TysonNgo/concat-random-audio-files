from pathlib import Path
from subprocess import Popen, PIPE
import json
import os
import random
import sys


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

def generate_ffmpeg_commands():
    """
    rtype: List(str)
    """
    ffmpeg = [
        f'{config["ffmpeg_path"]}',
        '-hide_banner',
        '-loglevel', 'panic'
    ]
    duration = config['duration_in_seconds']
    files_to_process = config['number_of_random_files']
    out_dir = config['out_dir']
    out_file_prefix = config['out_file_prefix']
    ext = config["extension"]
    intro = config['intro'] if 'intro' in config else ''

    files = get_file_list()
    random.shuffle(files)

    cmds = []

    for _ in range(files_to_process):
        length = 0
        prev_length, retries = length, 0
        inputs = []
        while length < duration:
            if retries > 10:
                print (f'Cannot create an audio file of {duration} seconds')
                sys.exit(1)

            if not files:
                files = get_file_list()
            f = files.pop()
            try:
                prev_length = length
                length += get_duration(f)
                inputs.append(str(f))
            except NotAnAudioFile as ex:
                print(ex)
                continue
            if prev_length == length:
                retries += 1

        out_file = os.path.join(out_dir,  f'{out_file_prefix}{_}.{ext}')

        if intro:
            inputs[:] = [intro] + inputs

        # [-i, file1, -i file2, ..., -i, fileN]
        ffmpeg_inputs = [
            option
            for pair in zip(['-i' for _ in range(len(inputs))], inputs)
            for option in pair
        ]

        filter_complex = [
            '-filter_complex',
            ''.join([f'[{i}:a]' for i in range(len(inputs))]) +
            f'concat=n={len(inputs)}:v=0:a=1 [out]',
            '-map', '[out]'
        ]

        # example ffmpeg command
        # "ffmpeg" -hide_banner -loglevel panic \
        # -i "path/to/first/file.mp3" -i "path/to/second/file.mp3" \
        # -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1 [out]" -map [out] \
        # -t 600 -y -c copy ".\out0.mp3"
        ffmpeg_cmd = [
            *ffmpeg,
            *ffmpeg_inputs,
            *filter_complex,
            '-t', str(duration),
            '-y',
            '-b:a', '192k',
            out_file
        ]

        print (ffmpeg_cmd)
        cmds.append(ffmpeg_cmd)
        break

    return cmds[::-1]

def spawn_ffmpeg_processes(commands):
    files_to_process = config['number_of_random_files']
    num_procs = config['number_of_concurrent_ffmpeg_processes']
    processes = []
    complete = 0
    while commands or (not commands and len(processes) > 0):
        if commands and len(processes) < num_procs:
            cmd = commands.pop()
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            processes.append(p)
        else:
            finished = []
            for i in range(len(processes)):
                processes[i].poll()
                if processes[i].returncode is not None:
                    finished.append(i)
                    complete += 1
                    print (f'{complete}/{files_to_process} audio files generated...')
            for i in finished:
                del processes[i]


def get_file_list():
    files = list(Path(config['in_dir']).glob('**/*'))
    return files

def get_duration(file):
    ffprobe = f'"{config["ffprobe_path"]}"'
    file = f'"{file}"'
    ffprobe_cmd = f'{ffprobe} -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i {file}'
    result = os.popen(ffprobe_cmd).read()
    try:
        return float(result)
    except:
        raise NotAnAudioFile(file)

with open('config.json') as f:
    config = json.load(f)
    assertConfig()

if __name__ == '__main__':
    cmds = generate_ffmpeg_commands()
    spawn_ffmpeg_processes(cmds)
    # TODO
    # generate ffmpeg commands and spawn
    # processes concurrently