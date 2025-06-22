from __future__ import annotations
 
import imp  # pylint: disable=deprecated-module
import importlib.util
import json
import logging
import os
import re
import sys
from collections import OrderedDict
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from importlib.resources import files
from typing import Any, Callable, Literal, TYPE_CHECKING, TypedDict
 
import pkg_resources
from celery.schedules import crontab
from flask import Blueprint
from flask_appbuilder.security.manager import AUTH_DB
from flask_caching.backends.base import BaseCache
from pandas import Series
from pandas._libs.parsers import STR_NA_VALUES  # pylint: disable=no-name-in-module
from sqlalchemy.orm.query import Query
 
from superset.advanced_data_type.plugins.internet_address import internet_address
from superset.advanced_data_type.plugins.internet_port import internet_port
from superset.advanced_data_type.types import AdvancedDataType
from superset.constants import CHANGE_ME_SECRET_KEY
from superset.jinja_context import BaseTemplateProcessor
from superset.key_value.types import JsonKeyValueCodec
from superset.stats_logger import DummyStatsLogger
from superset.superset_typing import CacheConfig
from superset.tasks.types import ExecutorType
from superset.utils import core as utils
from superset.utils.core import is_test, NO_TIME_RANGE, parse_boolean_string
from superset.utils.encrypt import SQLAlchemyUtilsAdapter
from superset.utils.log import DBEventLogger
from superset.utils.logging_configurator import DefaultLoggingConfigurator
 
logger = logging.getLogger(__name__)
 
if TYPE_CHECKING:
    from flask_appbuilder.security.sqla import models
 
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice
 
# Realtime stats logger, a StatsD implementation exists
STATS_LOGGER = DummyStatsLogger()
EVENT_LOGGER = DBEventLogger()
 
SUPERSET_LOG_VIEW = True
 
SECRET_KEY = 'YOUR_OWN_RANDOM_GENERATED_SECRET'
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://superset_user:superset@17.10.10.10:5432/superset_db'
##  # Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = False
#
TALISMAN_ENABLED = False
CONTENT_SECURITY_POLICY_WARNING = False
FAB_API_SWAGGER_UI = True
 
 
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_port": 1, "x_prefix": 1}
SUPERSET_WEBSERVER_TIMEOUT = int(timedelta(minutes=2).total_seconds())
 
 
# Nombre de mi APP
APP_NAME = "Superset"
 
# Para evitar DDOS
 
RATELIMIT_ENABLED = True
RATELIMIT_APPLICATION = "50 per second"
AUTH_RATE_LIMITED = True
AUTH_RATE_LIMIT = "5 per second"
RATELIMIT_STORAGE_URI = "redis://17.10.10.10:6379"
HTML_SANITIZATION = False
HTML_SANITIZATION_SCHEMA_EXTENSIONS  =False
 
# Modo de autentificacion
 
AUTH_TYPE = AUTH_DB
 
# Para los filtros
FILTER_SELECT_ROW_LIMIT = 50000
NATIVE_FILTER_DEFAULT_ROW_LIMIT = 50000
 
 
SQL_MAX_ROW = 20000000
 
# Setup default language
BABEL_DEFAULT_LOCALE = "en"
# Your application default translation path
BABEL_DEFAULT_FOLDER = "superset/translations"
# The allowed translation for your app
LANGUAGES = {
    "en": {"flag": "us", "name": "English"},
    "es": {"flag": "es", "name": "Spanish"},
    "it": {"flag": "it", "name": "Italian"},
    "fr": {"flag": "fr", "name": "French"},
    "zh": {"flag": "cn", "name": "Chinese"},
    "ja": {"flag": "jp", "name": "Japanese"},
    "de": {"flag": "de", "name": "German"},
    "pt": {"flag": "pt", "name": "Portuguese"},
    "pt_BR": {"flag": "br", "name": "Brazilian Portuguese"},
    "ru": {"flag": "ru", "name": "Russian"},
    "ko": {"flag": "kr", "name": "Korean"},
    "sk": {"flag": "sk", "name": "Slovak"},
    "sl": {"flag": "si", "name": "Slovenian"},
    "nl": {"flag": "nl", "name": "Dutch"},
}
# Turning off i18n by default as translation in most languages are
# incomplete and not well maintained.
LANGUAGES = {}
 
CURRENCIES = ["USD", "EUR", "GBP", "INR", "MXN", "JPY", "CNY", "PEN"]
 
FEATURE_FLAGS: dict[str, bool] = {
"ENABLE_JAVASCRIPT_CONTROLS": True,
"THUMBNAILS": True,
"DASHBOARD_CROSS_FILTERS": True,
"ALERT_REPORTS": True,
"ALERTS_ATTACH_REPORTS": True,
"HORIZONTAL_FILTER_BAR": True,
"SQLLAB_BACKEND_PERSISTENCE": True,
}
 
THUMBNAIL_SELENIUM_USER: str | None = "admin"
THUMBNAIL_EXECUTE_AS = [ExecutorType.CURRENT_USER, ExecutorType.SELENIUM]
THUMBNAIL_DASHBOARD_DIGEST_FUNC: None | (
    Callable[[Dashboard, ExecutorType, str], str]
) = None
THUMBNAIL_CHART_DIGEST_FUNC: Callable[[Slice, ExecutorType, str], str] | None = None
 
THUMBNAIL_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_NO_NULL_WARNING": True,
}
 
# Time before selenium times out after trying to locate an element on the page and wait
# for that element to load for a screenshot.
SCREENSHOT_LOCATE_WAIT = int(timedelta(seconds=10).total_seconds())
# Time before selenium times out after waiting for all DOM class elements named
# "loading" are gone.
SCREENSHOT_LOAD_WAIT = int(timedelta(minutes=1).total_seconds())
# Selenium destroy retries
SCREENSHOT_SELENIUM_RETRIES = 5
# Give selenium an headstart, in seconds
SCREENSHOT_SELENIUM_HEADSTART = 3
# Wait for the chart animation, in seconds
SCREENSHOT_SELENIUM_ANIMATION_WAIT = 5
# Replace unexpected errors in screenshots with real error messages
SCREENSHOT_REPLACE_UNEXPECTED_ERRORS = False
# Max time to wait for error message modal to show up, in seconds
SCREENSHOT_WAIT_FOR_ERROR_MODAL_VISIBLE = 5
# Max time to wait for error message modal to close, in seconds
SCREENSHOT_WAIT_FOR_ERROR_MODAL_INVISIBLE = 5
 
 
 
# PARA CACHE
 
CACHE_DEFAULT_TIMEOUT = int(timedelta(hours=1).total_seconds())
CACHE_CONFIG: CacheConfig = {"CACHE_TYPE": "RedisCache"}
DATA_CACHE_CONFIG: CacheConfig = {"CACHE_TYPE": "RedisCache"}
FILTER_STATE_CACHE_CONFIG: CacheConfig = {"CACHE_TYPE": "RedisCache",
                                          "CACHE_KEY_PREFIX": "superset_filter_cache",
                                          "CACHE_REDIS_URL": "redis://17.10.10.10:6379/0"
}
 
EXPLORE_FORM_DATA_CACHE_CONFIG: CacheConfig = {"CACHE_TYPE": "RedisCache"}    
 
# PARA SUBIR Y EXPORTAR CSV
EXCEL_EXTENSIONS = {"xlsx", "xls"}
CSV_EXTENSIONS = {"csv", "tsv", "txt"}
COLUMNAR_EXTENSIONS = {"parquet", "zip"}
ALLOWED_EXTENSIONS = {*EXCEL_EXTENSIONS, *CSV_EXTENSIONS, *COLUMNAR_EXTENSIONS}
 
CSV_EXPORT = {"encoding": "utf-8"}
EXCEL_EXPORT: dict[str, Any] = {}
 
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
#LOG_LEVEL = "INFO"
 
#LOG_LEVEL = "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
 
 
CELERY_BEAT_SCHEDULER_EXPIRES = timedelta(weeks=1)
 
 
class CeleryConfig:  # pylint: disable=too-few-public-methods
    broker_url = "redis://17.10.10.10:6379"
    imports = ("superset.sqllab",
               "superset.tasks",
               "superset.tasks.thumbnails",)
    result_backend = "redis://17.10.10.10:6379/0"
    worker_log_level = 'DEBUG'
    worker_prefetch_multiplier = 2
    task_acks_late = True
    task_annotations = {
        "sqllab.get_sql_results": {"rate_limit": "100/s"},
        "email_reports.send": {
            "rate_limit": "1/s",
            "time_limit": int(timedelta(seconds=120).total_seconds()),
            "soft_time_limit": int(timedelta(seconds=150).total_seconds()),
            "ignore_result": True,
        },
    }
    beat_schedule = {
        "email_reports.schedule_hourly": {
            "task": "email_reports.schedule_hourly",
            "schedule": crontab(minute=1, hour="*"),
        },
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
            "options": {"expires": int(CELERY_BEAT_SCHEDULER_EXPIRES.total_seconds())},
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=0, hour=0),
        },
    }
from flask_caching.backends.rediscache import RedisCache
 
RESULTS_BACKEND = RedisCache(
    host='17.10.10.10', port=6379, key_prefix='sql_lab')
RESULTS_BACKEND_USE_MSGPACK = True
 
 
# Async selenium thumbnail task will use the following user
THUMBNAIL_SELENIUM_USER = "admin"
ALERT_REPORTS_EXECUTE_AS = [ExecutorType.SELENIUM]
 
 
CELERY_CONFIG = CeleryConfig  # pylint: disable=invalid-name
 
 
 
SQLLAB_DEFAULT_DBID = None
SQLLAB_ASYNC_TIME_LIMIT_SEC = int(timedelta(hours=6).total_seconds())
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = int(timedelta(seconds=10).total_seconds())
 
QUERY_COST_FORMATTERS_BY_ENGINE: dict[
    str, Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
] = {}
 
# smtp server configuration
EMAIL_NOTIFICATIONS = False  # all the emails are sent using dryrun
SMTP_HOST = "17.10.10.10"
SMTP_STARTTLS = True
SMTP_SSL = False
# SMTP_USER = "superset"
SMTP_PORT = 25
# SMTP_PASSWORD =
SMTP_MAIL_FROM = "example@gmail.com"
# If True creates a default SSL context with ssl.Purpose.CLIENT_AUTH using the
# default system root CA certificates.
SMTP_SSL_SERVER_AUTH = False
ENABLE_CHUNK_ENCODING = False
 
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False
WEBDRIVER_TYPE = "chrome"
 
GLOBAL_ASYNC_QUERIES_REDIS_CONFIG = {
    "port": 6379,
    "host": "17.10.10.10",
    "password": "",
    "db": 0,
    "ssl": False,
}
 