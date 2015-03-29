import vim

with open('plugin/commands', 'r') as command_file:
    commands = command_file.readlines()

for command in commands:
    command = command.rstrip()
    vim.command("autocmd " + command + " * :call VPLogInfo('" + command + "')")
