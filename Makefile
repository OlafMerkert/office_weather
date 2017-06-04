UDEV_FILE=50-holtek.rules

run :
	python2 monitor.py /dev/co2sensor

setup-udev :
	sudo cp $(UDEV_FILE) /etc/udev/rules.d/$(UDEV_FILE)

install-debian :
	sudo apt-get install python-pip python-dev libyaml-dev

install-fedora :
	sudo dnf install python-pip python-devel libyaml-devel

install-dependencies :
	pip install --user requests pyyaml
