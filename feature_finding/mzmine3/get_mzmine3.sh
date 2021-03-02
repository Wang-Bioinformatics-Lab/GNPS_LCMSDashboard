# download mzmine-ubuntu artifact for latest build
# wget --no-check-certificate https://nightly.link/robinschmid/mzmine3/actions/artifacts/44356954.zip
# download latest release
wget https://github.com/robinschmid/mzmine3/releases/download/v3-beta1/MZmine_package_ubuntu-latest.zip

# clear downloads
rm -rf ./tmp_download
# unzip -d ./tmp_download/ 44356954.zip
unzip -d ./tmp_download/ MZmine_package_ubuntu-latest.zip

# install xdg dependency
# somehow on WSL xdg needed this directory - otherwise error
# sudo mkdir /usr/share/desktop-directories/
sudo apt-get install xdg-utils

# install mzmine
sudo apt install ./tmp_download/mzmine*.deb
# dpkg --status mzmine

# run mzmine with batch -b and -p / --pref for preferences file
# /opt/mzmine/bin/MZmine -b

