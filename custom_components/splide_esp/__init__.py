from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import datetime

import logging
import requests

from .const import DOMAIN, ESP_BSE_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, entry)
    hass.data[DOMAIN][entry.entry_id] = MyAPI(hass, entry.data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MyAPI:
    def __init__(self, hass, config) -> None:
        super().__init__()
        self.config = config
        self.hass = hass

    def getData(self, location_id, api_key):
        api_url = ESP_BSE_URL + "/area?id=" + location_id
        # + "&test=current"
        _LOGGER.info("URL: " + api_url)
        _LOGGER.info("API_Key: " + api_key)
        headers = {"token": api_key}
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            _LOGGER.info(response)

    async def fetch_data(self) -> any:
        _LOGGER.warning("Fetch Data from my api")
        api_key = self.config["api_key"]
        location_id = self.config["location_id"]

        response = await self.hass.async_add_executor_job(
            self.getData, location_id, api_key
        )

        if len(response["events"]) > 0:
            value_end = datetime.datetime.fromisoformat(response["events"][0]["end"])
            value_start = datetime.datetime.fromisoformat(
                response["events"][0]["start"]
            )
            now = datetime.datetime.now().astimezone(value_start.tzinfo)

            current_end = None
            next_start = None
            next_end = None

            if value_start < now:
                current_end = value_end
                if len(response["events"]) > 1:
                    next_end = datetime.datetime.fromisoformat(
                        response["events"][1]["end"]
                    )
                    next_start = datetime.datetime.fromisoformat(
                        response["events"][1]["start"]
                    )
            else:
                next_start = value_start
                next_end = value_end

        return {
            "current_loadshedding_end": current_end,
            "next_loadshedding_start": next_start,
            "next_loadshedding_end": next_end,
            # "current_loadshedding_stage": 7,
        }
