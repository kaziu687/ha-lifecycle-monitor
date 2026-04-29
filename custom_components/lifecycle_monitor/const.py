"""Constants for lifecycle_monitor."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "lifecycle_monitor"

CONF_NAME = "name"
CONF_DEVICE_TYPE = "device_type"
# Shared
CONF_LAST_REPLACED = "last_replaced"
# Virtual Battery
CONF_BATTERY_LIFESPAN = "battery_lifespan"
CONF_LOW_THRESHOLD = "low_threshold_days"
# Maintenance Interval
CONF_INTERVAL_DAYS = "interval_days"
CONF_WARNING_THRESHOLD = "warning_threshold_days"
# Fixed Date
CONF_END_DATE = "end_date"

DEVICE_TYPE_BATTERY = "battery"
DEVICE_TYPE_MAINTENANCE = "maintenance"
DEVICE_TYPE_FIXED_DATE = "fixed_date"
