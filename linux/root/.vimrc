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

autocmd FileType make set noexpandtab
autocmd Filetype html setlocal ts=2 sw=2 expandtab
autocmd Filetype ruby setlocal ts=2 sw=2 expandtab
autocmd Filetype javascript setlocal ts=4 sw=4 sts=0 expandtab
autocmd Filetype coffeescript setlocal ts=4 sw=4 sts=0 expandtab
autocmd Filetype jade setlocal ts=4 sw=4 sts=0 expandtab

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

autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab
