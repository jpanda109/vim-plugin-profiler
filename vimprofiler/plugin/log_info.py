import vim
command = vim.eval('a:command')
with open("test.txt", 'w') as f:
    f.write(command)
