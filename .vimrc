syntax on
set tabstop=4
set softtabstop=0
set noexpandtab
set laststatus=1
set ruler
"set encoding=utf-8
"set fileencodings=utf-8

syntax on
filetype indent plugin on
set modeline
set shiftwidth=4
set background=dark
set hlsearch
set spell spelllang=en_us

"Restore last position
function! ResCur()
  if line("'\"") <= line("$")
    normal! g`"
    return 1
  endif
endfunction

augroup resCur
  autocmd!
  autocmd BufWinEnter * call ResCur()
augroup END
