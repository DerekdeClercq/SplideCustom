from __future__ import annotations

from datetime import timedelta
from collections.abc import Callable
from dataclasses import dataclass
import logging

import async_timeout

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class ESPEntityDescriptionValue:
    value: Callable[[dict]]


@dataclass
class ESPDescription(SensorEntityDescription, ESPEntityDescriptionValue):
    """Describes ESP sensor entity."""


SENSOR_TYPES: list[ESPDescription] = [
    ESPDescription(
        key="current_loadshedding_end",
        name="Current Loadshedding End",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data.get("current_loadshedding_end"),
    ),
    ESPDescription(
        key="next_loadshedding_end",
        name="Next Loadshedding End",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data.get("next_loadshedding_end"),
    ),
    ESPDescription(
        key="next_loadshedding_start",
        name="Next Loadshedding Start",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data.get("next_loadshedding_start"),
    ),
    # ESPDescription(
    #     key="current_loadshedding_stage",
    #     name="Current Loadshedding Stage",
    #     state_class=SensorStateClass.MEASUREMENT,
    #     value=lambda data: data.get("current_loadshedding_stage"),
    # ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    my_api = hass.data[DOMAIN][entry.entry_id]
    coordinator = SplideCoordinator(hass, my_api)

    await coordinator.async_config_entry_first_refresh()

    entities: list[SplideEntity] = []
    for description in SENSOR_TYPES:
        entities.append(SplideEntity(coordinator, description))

    async_add_entities(entities)


class SplideCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, my_api):
        super().__init__(
            hass,
            _LOGGER,
            name="Splide ESP Sensor",
            update_interval=timedelta(minutes=my_api.config["interval"]),
        )
        self.my_api = my_api

    async def _async_update_data(self):
        async with async_timeout.timeout(10):
            return await self.my_api.fetch_data()

        # TODO
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")


class SplideEntity(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SplideCoordinator, description: ESPDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description: ESPDescription = description
        self._attr_name = description.name
        self._attr_native_value = description.value(coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.entity_description.value(self.coordinator.data)
        self.async_write_ha_state()
