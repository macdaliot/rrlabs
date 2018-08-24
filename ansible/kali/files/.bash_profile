# ~/..bash_profile: executed by bash(1) for login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# settint PATH
export PATH=~/bin:~/.local/bin:$PATH

# start ssh-agent
if [ -z "$SSH_AUTH_SOCK" ] ; then
	eval `ssh-agent -s` > /dev/null 2>&1
fi

# Fixing missing SIGWINCH signals that mess up screen
export PROMPT_COMMAND="resize &>/dev/null;$PROMPT_COMMAND"
