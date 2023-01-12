"""Config flow for splide_esp integration."""
from __future__ import annotations

from typing import Any
import logging
from .const import DOMAIN
from .const import ESP_BSE_URL
import requests

import voluptuous as vol

from homeassistant.helpers.selector import selector
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult


_LOGGER = logging.getLogger(__name__)

STEP_API_KEY = vol.Schema(
    {
        vol.Required("api_key"): str,
        vol.Required("area"): str,
        vol.Required("interval", default=30): int,
    }
)


class SplideConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def getLocations(self, area, api_key):
        api_url = ESP_BSE_URL + "/areas_search?text=" + area
        _LOGGER.info("URL: " + api_url)
        _LOGGER.info("API_Key: " + api_key)
        headers = {"token": api_key}
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            _LOGGER.info("Good response")
            _LOGGER.info(response.json())
            data = response.json()
            result = [None] * len(data["areas"])
            counter = 0
            result = [None] * len(data["areas"])
            for area in data["areas"]:
                result[counter] = (area["id"], area["name"], area["region"])
                counter = counter + 1

            return result
        else:
            _LOGGER.info(response)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        # errors = {}
        # if user_input is not None:
        # Validate user input
        _LOGGER.info(user_input)

        if user_input is None:
            _LOGGER.info("Screen 1")
            return self.async_show_form(step_id="user", data_schema=STEP_API_KEY)
        elif "location" not in user_input.keys():
            self.init_info = user_input
            _LOGGER.info("Screen 2")
            _LOGGER.info("Load Data")
            response = await self.hass.async_add_executor_job(
                self.getLocations, user_input["area"], user_input["api_key"]
            )
            self.lastResponse = response
            it = map(lambda x: x[1], response)
            values = list(it)
            _LOGGER.info(values)

            dataSchema = {}
            dataSchema["location"] = selector({"select": {"options": values}})

            STEP_USER_LOCATION = vol.Schema(dataSchema)

            return self.async_show_form(step_id="user", data_schema=STEP_USER_LOCATION)
        else:
            _LOGGER.info("Saving:")

            filtered = list(
                filter(
                    lambda entry: entry[1] == user_input["location"], self.lastResponse
                )
            )
            saveData = {
                "location_id": filtered[0][0],
                "location_name": filtered[0][1],
                "location_area": filtered[0][2],
                "api_key": self.init_info["api_key"],
                "interval": self.init_info["interval"],
            }
            _LOGGER.info(saveData)
            return self.async_create_entry(title="Splide ESP", data=saveData)
