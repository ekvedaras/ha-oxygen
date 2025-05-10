"""Sensor platform for Recuperator integration."""
import logging
import asyncio
import aiohttp
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

# Update interval
UPDATE_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Recuperator sensors."""
    host = hass.data[entry.entry_id]["host"]
    session = hass.data[entry.entry_id]["session"]

    # Create the data coordinator
    coordinator = RecuperatorDataCoordinator(hass, host, session)

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Create entities
    entities = [
        RecuperatorPowerSensor(coordinator, entry),
        RecuperatorSetTemperatureSensor(coordinator, entry),
        RecuperatorTemperatureSensor(coordinator, entry),
        RecuperatorHumiditySensor(coordinator, entry),
    ]

    async_add_entities(entities)

class RecuperatorDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Recuperator data."""

    def __init__(self, hass, host, session):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Recuperator",
            update_interval=UPDATE_INTERVAL,
        )
        self.host = host
        self.session = session

    async def _async_update_data(self):
        """Fetch data from the device."""
        data = {}

        try:
            # Get current power
            async with self.session.get(f"http://{self.host}/cmd?gr1", timeout=5) as response:
                if response.status == 200:
                    power_text = await response.text()
                    try:
                        data["power"] = int(power_text.strip())
                    except ValueError:
                        _LOGGER.error("Failed to parse power value: %s", power_text)

            # Get set temperature
            async with self.session.get(f"http://{self.host}/cmd?gr2", timeout=5) as response:
                if response.status == 200:
                    temp_text = await response.text()
                    try:
                        data["set_temperature"] = float(temp_text.strip())
                    except ValueError:
                        _LOGGER.error("Failed to parse set temperature value: %s", temp_text)

            # Get current temperature
            async with self.session.get(f"http://{self.host}/cmd?gi2", timeout=5) as response:
                if response.status == 200:
                    temp_text = await response.text()
                    try:
                        data["temperature"] = float(temp_text.strip())
                    except ValueError:
                        _LOGGER.error("Failed to parse temperature value: %s", temp_text)

            # Get humidity
            async with self.session.get(f"http://{self.host}/cmd?gi3", timeout=5) as response:
                if response.status == 200:
                    humidity_text = await response.text()
                    try:
                        data["humidity"] = int(humidity_text.strip())
                    except ValueError:
                        _LOGGER.error("Failed to parse humidity value: %s", humidity_text)

            return data

        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with device: %s", err)
            raise
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error: %s", err)
            raise

class RecuperatorBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for all Recuperator sensors."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry_id = entry.entry_id
        self._attr_has_entity_name = True

class RecuperatorPowerSensor(RecuperatorBaseSensor):
    """Sensor to track current power level."""

    _attr_name = "Power"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:fan"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry_id}_power"

    @property
    def native_value(self):
        """Return the power level."""
        if self.coordinator.data and "power" in self.coordinator.data:
            return self.coordinator.data["power"]
        return None

class RecuperatorSetTemperatureSensor(RecuperatorBaseSensor):
    """Sensor to track set temperature."""

    _attr_name = "Set Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry_id}_set_temperature"

    @property
    def native_value(self):
        """Return the set temperature."""
        if self.coordinator.data and "set_temperature" in self.coordinator.data:
            return self.coordinator.data["set_temperature"]
        return None

class RecuperatorTemperatureSensor(RecuperatorBaseSensor):
    """Sensor to track current temperature."""

    _attr_name = "Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry_id}_temperature"

    @property
    def native_value(self):
        """Return the current temperature."""
        if self.coordinator.data and "temperature" in self.coordinator.data:
            return self.coordinator.data["temperature"]
        return None

class RecuperatorHumiditySensor(RecuperatorBaseSensor):
    """Sensor to track humidity."""

    _attr_name = "Humidity"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry_id}_humidity"

    @property
    def native_value(self):
        """Return the humidity value."""
        if self.coordinator.data and "humidity" in self.coordinator.data:
            return self.coordinator.data["humidity"]
        return None