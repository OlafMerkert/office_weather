UDEV_FILE=50-holtek.rules

run :
	python2 monitor.py /dev/co2sensor

install-udev :
	sudo cp $(UDEV_FILE) /etc/udev/rules.d/$(UDEV_FILE)
