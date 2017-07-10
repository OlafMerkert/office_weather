UDEV_FILE=50-holtek.rules
FAILED_MESSAGE="zenity  --notification --window-icon='dialog-warning-symbolic' --text='Tests for office_weather failed!'"


run :
	python3 monitor.py /dev/co2sensor

watch_test :
	ptw --config "pytest.ini" --onfail $(FAILED_MESSAGE) -- -v .

run-device :
	python3 Co2Device.py /dev/co2sensor

collect-log :
	python3 datalog.py /dev/co2sensor

setup-udev :
	sudo cp $(UDEV_FILE) /etc/udev/rules.d/$(UDEV_FILE)

install-debian :
	sudo apt-get install python-pip python-dev libyaml-dev

install-fedora :
	sudo dnf install python-pip python-devel libyaml-devel

install-dependencies :
	pip install --user requests pyyaml
