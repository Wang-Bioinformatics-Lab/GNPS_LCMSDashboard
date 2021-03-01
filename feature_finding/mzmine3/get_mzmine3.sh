# download mzmine-ubuntu artifact for latest build
wget --no-check-certificate https://nightly.link/robinschmid/mzmine3/actions/artifacts/44340837.zip
# download latest release
# wget https://github.com/mzmine/mzmine2/releases/download/v2.53/MZmine-2.53-Linux.zip

# clear downloads
rm -rf ./tmp_download
unzip -d ./tmp_download/ 44340837.zip

# install xdg dependency
# somehow on WSL xdg needed this directory - otherwise error
# sudo mkdir /usr/share/desktop-directories/
sudo apt-get install xdg-utils

# install mzmine
sudo apt install ./tmp_download/mzmine*.deb
# dpkg --status mzmine

# run mzmine with batch -b and -p / --pref for preferences file
# /opt/mzmine/bin/MZmine -b

