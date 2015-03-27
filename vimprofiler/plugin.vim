function! VPLogInfo(command)
    pyfile plugin/log_info.py
endfunc

command! VPLogInfo call VPLogInfo()
