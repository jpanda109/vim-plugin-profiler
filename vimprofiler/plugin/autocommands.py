import vim
import time

#Takes the commands, reads them, and sends them to VPLogInfo
#Which then sends it to the python script

with open('plugin/commands', 'r') as command_file:
    commands = command_file.readlines()

start_time = time.time()

for command in commands:
    command = command.rstrip()
    vim.command("autocmd " + command + " * :call VPLogInfo('"
        + command + "','" + str(start_time) + "')")
