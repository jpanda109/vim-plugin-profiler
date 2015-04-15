import vim
import time

with open('plugin/commands', 'r') as command_file:
    commands = command_file.readlines()

start_time = time.time()

for command in commands:
    command = command.rstrip()
    vim.command("autocmd " + command + " * :call VPLogInfo('" 
        + command + "','" + str(start_time) + "')")
