"""Config flow for Bbox Plus integration."""

from typing import Any, override

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

class ProfilerConfigFlow(ConfigFlow, domain='bboxplus'):
    """Handle a config flow for Bbox Plus."""

    VERSION = 0
    MINOR_VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title='Bbox', data={})
        return self.async_show_form(step_id="user")
