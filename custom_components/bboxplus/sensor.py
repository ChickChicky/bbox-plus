"""Extended support for Bbox Bouygues Modem Router."""

from datetime import timedelta
import logging

import probatio

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription
)

from homeassistant.const import CONF_MONITORED_VARIABLES, CONF_NAME, UnitOfDataRate, UnitOfTime, UnitOfInformation, UnitOfRatio
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import get_device, get_wan_info, get_wan_stats

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Bbox"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

SENSOR_DESCS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription( key="down_rate_max",
        name="Maximum Download Bandwidth",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download",
    ),
    SensorEntityDescription( key="up_rate_max",
        name="Maximum Upload Bandwidth",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload",
    ),
    SensorEntityDescription( key="down_rate_current",
        name="Currently Used Download Bandwidth",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download",
    ),
    SensorEntityDescription( key="up_rate_current",
        name="Currently Used Upload Bandwidth",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload"
    ),
    SensorEntityDescription( key="down_bytes",
        name="Downloaded bytes",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transfer-down",
    ),
    SensorEntityDescription( key="up_bytes",
        name="Uploaded bytes",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transfer-up",
    ),
    SensorEntityDescription( key="down_packets",
        name="Downloaded packets",
        state_class=SensorStateClass.TOTAL,
        icon="mdi:package-down",
    ),
    SensorEntityDescription( key="up_packets",
        name="Uploaded packets",
        state_class=SensorStateClass.TOTAL,
        icon="mdi:package-up",
    ),
    SensorEntityDescription( key="down_packets_errors",
        name="Download packets errors",
        icon="mdi:download-off",
    ),
    SensorEntityDescription( key="up_packets_errors",
        name="Upload packets errors",
        icon="mdi:upload-off",
    ),
    SensorEntityDescription( key="down_packets_discards",
        name="Dowload packets discards",
        icon="mdi:download-off",
    ),
    SensorEntityDescription( key="up_packets_discards",
        name="Upload packets discards",
        icon="mdi:upload-off",
    ),
    SensorEntityDescription( key="down_occupation",
        name="Download Occupation",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:pan-down",
    ),
    SensorEntityDescription( key="up_occupation",
        name="Upload Occupation",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:pan-up",
    ),
    SensorEntityDescription( key="number_of_reboots",
        name="Number of reboots",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:restart",
    ),
    SensorEntityDescription( key="uptime",
        name="Uptime",
        # device_class=SensorDeviceClass.UPTIME, # TODO: Zas ist bad
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:progress-clock",
    ),
)

BINARY_SENSOR_DESCS: tuple[BinarySensorEntityDescription] = (
    BinarySensorEntityDescription( key="wan_status",
        name="WAN Status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:network-outline"
    ),
)

SENSOR_KEYS: list[str] = [desc.key for desc in SENSOR_DESCS + BINARY_SENSOR_DESCS]

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        probatio.Optional(CONF_MONITORED_VARIABLES, default=SENSOR_KEYS): probatio.All(
            cv.ensure_list, [probatio.In(SENSOR_KEYS)]
        ),
        probatio.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Bbox sensor."""

    name = config[CONF_NAME]
    monitored_variables = config[CONF_MONITORED_VARIABLES]

    entities: list[BboxSensor|BboxBinarySensor] = []

    entities.extend((
        BboxSensor(name, description)
        for description in SENSOR_DESCS
        if description.key in monitored_variables
    ))
    entities.extend((
        BboxBinarySensor(name, description)
        for description in BINARY_SENSOR_DESCS
        if description.key in monitored_variables
    ))

    add_entities(entities, True)

class BboxBinarySensor(BinarySensorEntity):
    """Implementation of Bbox binary sensors."""

    def __init__(self, name, description: BinarySensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._attr_name = f"{name} {description.name}"

    def update(self) -> None:
        """Get the latest data from Bbox and update the state."""

        try:
            match self.entity_description.key:
                case 'wan_status':
                    self._attr_icon = 'mdi:help-network-outline'
                    self._attr_is_on = get_wan_info().ip.state == 'Up'
                    self._attr_icon = 'mdi:check-network-outline' if self._attr_is_on else 'mdi:close-network-outline'
                case k:
                    raise KeyError('Unknown binary sensor %r'%k)
            self._attr_available = True

        except BaseException as e:
            self._attr_available = False
            raise e

class BboxSensor(SensorEntity):
    """Implementation of Bbox sensors."""

    def __init__(self, name, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._attr_name = f"{name} {description.name}"

    def update(self) -> None:
        """Get the latest data from Bbox and update the state."""

        try:
            match self.entity_description.key:
                case 'down_rate_max':
                    self._attr_native_value = get_wan_stats().rx.maxBandwidth
                case 'up_rate_max':
                    self._attr_native_value = get_wan_stats().tx.maxBandwidth
                case 'down_rate_current':
                    self._attr_native_value = get_wan_stats().rx.bandwidth
                case 'up_rate_current':
                    self._attr_native_value = get_wan_stats().tx.bandwidth
                case 'down_bytes':
                    self._attr_native_value = get_wan_stats().rx.bytes
                case 'up_bytes':
                    self._attr_native_value = get_wan_stats().tx.bytes
                case 'down_packets':
                    self._attr_native_value = get_wan_stats().rx.packets
                case 'up_packets':
                    self._attr_native_value = get_wan_stats().tx.packets
                case 'down_packets_errors':
                    self._attr_native_value = get_wan_stats().rx.packetserrors
                case 'up_packets_errors':
                    self._attr_native_value = get_wan_stats().tx.packetserrors
                case 'down_packets_discards':
                    self._attr_native_value = get_wan_stats().rx.packetsdiscards
                case 'up_packets_discards':
                    self._attr_native_value = get_wan_stats().tx.packetsdiscards
                case 'down_occupation':
                    self._attr_native_value = get_wan_stats().rx.occupation/10
                case 'up_occupation':
                    self._attr_native_value = get_wan_stats().tx.occupation/10
                case 'number_of_reboots':
                    self._attr_native_value = get_device().numberofboots
                case 'uptime':
                    self._attr_native_value = get_device().uptime
                case k:
                    raise KeyError('Unknown sensor %r'%k)
            self._attr_available = True

        except BaseException as e:
            self._attr_available = False
            raise e

