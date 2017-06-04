# what & why?

Measuring CO2 and Temperature at [TNG](https://www.tngtech.com/).

People are sensitive to high levels of CO2 or uncomfortably hot work environments. Running air conditioning makes a lot of noise, which can annoy people, too. So we want notifications on CO2 levels and temperature, to slack.

# requirements

## hardware

1) [TFA-Dostmann AirControl Mini CO2 Messgerät](http://www.amazon.de/dp/B00TH3OW4Q) -- 80 Euro

2) any Linux system with a USB port and Python 2

# installation

1) install Python and dependencies (needs sudo)

```
make install-debian  # on Ubuntu or other Debian based systems
make install-fedora  # on Fedora

make install-dependencies  # pip dependencies
```

2)  You can configure this bot to automatically post to a Slack channel.
Just add an "Incoming Webhook" to your Slack team's integrations and add a `slack` hash to the config file (see config.yaml.sample for the precise config file structure). 


3) fix socket permissions: install udev rules
```
make setup-udev
```

4) run the script
```
make run
```
The configuration is named config.yaml and should be in the same directory as the script.



# credits

forked from [wooga/office_weather](https://github.com/wooga/office_weather), which in turn is based on code by [henryk ploetz](https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us)

# license

[MIT](http://opensource.org/licenses/MIT)
