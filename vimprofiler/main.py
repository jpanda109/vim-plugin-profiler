import subprocess


args = ['gnome-terminal', '-x', 'sh', '-c',
        'vim --startuptime vimprofile-startuptime.log -S plugin.vim; bash']
subprocess.call(args)
