
eval "$(/opt/homebrew/bin/brew shellenv zsh)"

# Setting PATH for Python 3.13
# The original version is saved in .zprofile.pysave
PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:${PATH}"
export PATH

# Added by Obsidian
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
