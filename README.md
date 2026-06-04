# Osprey Charging for Home Assistant

This is a custom integration for Home Assistant that adds [Osprey Charging](https://www.ospreycharging.co.uk/) electric vehicle (EV) charging locations to Home Assistant. 

The charging stations are represented as devices with sensors for the number of total and currently available chargers for different connectors (CCS, CHAdeMO), along with location information.


> [!CAUTION]
> This project includes code produced with a "generative AI". This is documented here for transparency.


## License

This project uses the MIT license.

> [!WARNING]
> This project is entirely unaffiliated with Osprey Charging Network Ltd

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stupidpupil&repository=ha-osprey-charging&category=integration)

## Configuration

This integration does _not_ have a user-friendly "configuration flow". Instead, you must edit your `configuration.yaml` file to include an `osprey_charging` entry.

An example configruation entry is given below:

```yaml

osprey_charging:
  scan_interval: 300   # optional, seconds — default is 300 (5 minutes)
  station_ids:
    - GB-OSP-d422eff3ae0349309973d356d1847095 # Morrisons, Workington
    - GB-OSP-5038818a181440aea6a7616565f02d66 # Allison Court, Gateshead

```

You can find charging station IDs by browsing the [Osprey Charging network map](https://www.ospreycharging.co.uk/find-our-ev-charging-stations) and using your browser's developer tools to look for requests to `https://apigw.ospreycharging.co.uk` when clicking on a charging station.
