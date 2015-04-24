

"Vim plugin calls.
"These are wrappers so that we dont have to write this tool in vimscript,
"we can write it in python instead.

function! VPLogInfo(command,start_time)
    let s:current_file=expand('<sfile>:p:h')
    let s:pyscript = s:current_file . "/plugin/log_info.py"
    execute 'pyfile ' . s:pyscript
endfunc

command! VPLogInfo call VPLogInfo()


function! AutoLogInfo()
    let s:current_dir=expand('<sfile>:p:h')
    let s:pyscript = s:current_dir . "/plugin/autocommands.py"
    execute 'pyfile ' . s:pyscript
endfunc

command! AutoLogInfo call AutoLogInfo()
