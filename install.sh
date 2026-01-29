#!/bin/bash

# Output

function starting() {
    echo -e "\xF0\x9F\x9A\x80  \e[32mStarting: $1\e[0m"
}

function success() {
    echo -e "\xF0\x9F\x8F\x81  \e[32mSUCCESS: $1\e[0m"
}

function failure() {
    echo -e "\xF0\x9F\x92\xA5  \e[31mFAIL: $1\e[0m"
}

# Install packages

if ! [ -x "$(command -v brew)" ]; then
  starting "install brew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

if ! [ -x "$(command -v gls)" ]; then
  starting "install coreutils"
  brew install coreutils
fi

if ! [ -x "$(command -v pyenv)" ]; then
  starting "install pyenv"
  brew install pyenv
fi

# Source zsh
starting "source zshrc"
ln -s ~/dotfiles/.zshrc ~/.zshrc
source ~/.zshrc

starting "link remaining dotfiles"
ln -s ~/dotfiles/.gitconfig ~/.gitconfig
ln -s ~/dotfiles/.gitignore_global ~/.gitignore_global
ln -s ~/dotfiles/.inputrc ~/.inputrc
ln -s ~/dotfiles/.lesshst ~/.lesshst
ln -s ~/dotfiles/.pyrc ~/.pyrc
ln -s ~/dotfiles/.serverlessrc ~/.serverlessrc

success "setup complete!"
