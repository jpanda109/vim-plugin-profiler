with open('commands', 'r') as command_file:
    commands = command_file.readlines()

for command in commands:
    command = command.rstrip()
    print("autocmd " + command + " * :call VPLogInfo('" + command + "')")
