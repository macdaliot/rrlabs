if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# start ssh-agent
if [ -z "$SSH_AUTH_SOCK" ] ; then
	eval `ssh-agent -s` > /dev/null 2>&1
fi
