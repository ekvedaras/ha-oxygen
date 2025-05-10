"""Fan platform for Recuperator integration."""
import logging
import aiohttp

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.util.percentage import (
    int_states_in_range,
    ranged_value_to_percentage,
    percentage_to_ranged_value,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .sensor import RecuperatorDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Define speed range
SPEED_RANGE = (1, 100)  # min, max

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Recuperator fan platform."""
    coordinator = hass.data[entry.entry_id].get("coordinator")
    host = hass.data[entry.entry_id]["host"]
    session = hass.data[entry.entry_id]["session"]

    # Create coordinator if it doesn't exist yet
    if coordinator is None:
        coordinator = RecuperatorDataCoordinator(hass, host, session)
        await coordinator.async_config_entry_first_refresh()
        hass.data[entry.entry_id]["coordinator"] = coordinator

    # Create fan entity
    async_add_entities([RecuperatorFan(coordinator, entry, host, session)])

class RecuperatorFan(CoordinatorEntity, FanEntity):
    """Representation of a Recuperator fan."""

    _attr_name = "Recuperator"
    _attr_supported_features = FanEntityFeature.SET_SPEED
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, host, session):
        """Initialize the fan."""
        super().__init__(coordinator)
        self.entry_id = entry.entry_id
        self.host = host
        self.session = session

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry_id}_fan"

    @property
    def is_on(self):
        """Return true if the fan is on."""
        if self.coordinator.data and "power" in self.coordinator.data:
            return self.coordinator.data["power"] > 0
        return False

    @property
    def percentage(self):
        """Return the current speed percentage."""
        if self.coordinator.data and "power" in self.coordinator.data:
            return ranged_value_to_percentage(SPEED_RANGE, self.coordinator.data["power"])
        return None

    @property
    def speed_count(self):
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    async def async_set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            power = round(percentage_to_ranged_value(SPEED_RANGE, percentage))
            await self._set_power(power)

    async def async_turn_on(
        self, percentage=None, preset_mode=None, **kwargs
    ):
        """Turn on the fan."""
        if percentage is None:
            # If no percentage provided, use 50%
            percentage = 50

        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
        """Turn off the fan."""
        await self._set_power(0)

    async def _set_power(self, power):
        """Set the power level of the device."""
        try:
            url = f"http://{self.host}/cmd?sr1={power}"
            async with self.session.get(url, timeout=5) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set power: %s", response.status)
                    return

            # Request an immediate data update
            await self.coordinator.async_request_refresh()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting power: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error: %s", err)