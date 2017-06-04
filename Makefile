UDEV_FILE=50-holtek.rules

install-udev :
	sudo cp $(UDEV_FILE) /etc/udev/rules.d/$(UDEV_FILE)
