"""Config flow for Recuperator integration."""
import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from . import DEFAULT_HOST

_LOGGER = logging.getLogger(__name__)

# Define schema for config flow
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
})

class RecuperatorConfigFlow(config_entries.ConfigFlow, domain="recuperator"):
    """Handle a config flow for Recuperator integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            # Try to connect to the device
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{host}/cmd?gr1", timeout=5) as response:
                        if response.status == 200:
                            # Connection successful, create entry
                            return self.async_create_entry(
                                title=f"Recuperator ({host})",
                                data={CONF_HOST: host},
                            )
                        else:
                            errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )