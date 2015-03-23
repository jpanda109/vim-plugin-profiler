import subprocess


def run_main_process():
    args = ['python3', 'src/mainprocess.py']
    subprocess.call(args)

run_main_process()
