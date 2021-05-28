import logging
import os


def get_logging_level(env_variable_name, default=logging.NOTSET):
    if not isinstance(default, int):
        default = logging.NOTSET
    _value = os.getenv(env_variable_name, default)
    if _value == default:
        _level = _value
    else:
        _level = getattr(logging, _value, default)
        if not isinstance(_level, int):
            _level = default
    return _level


STREAM2PY_LOGGING_LEVEL = get_logging_level(
    env_variable_name='STREAM2PY_LOGGING_LEVEL', default=logging.WARNING
)


def set_logging_config(level=STREAM2PY_LOGGING_LEVEL, filename=None):
    logging.basicConfig(
        filename=filename,
        level=level,
        datefmt='%d-%m-%y %H:%M',
        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d  ::> %(message)s',
    )
