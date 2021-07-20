"""
Import as:

import helpers.s3 as hs3
"""

import configparser
import functools
import logging
import os
import pprint
from typing import Any, Dict, Optional

_WARNING = "\033[33mWARNING\033[0m"

try:
    pass
except ModuleNotFoundError:
    _module = "boto3"
    print(_WARNING + f": Can't find {_module} : continuing")

try:
    import s3fs
except ModuleNotFoundError:
    _module = "s3fs"
    print(_WARNING + f": Can't find {_module}: continuing")


import helpers.dbg as dbg  # noqa: E402 module level import not at top of file  # pylint: disable=wrong-import-position

_LOG = logging.getLogger(__name__)


def _get_aws_config(file_name: str) -> configparser.RawConfigParser:
    file_name = os.path.join(os.path.expanduser("~"), ".aws", file_name)
    # assert 0
    dbg.dassert_file_exists(file_name)
    # Read the config.
    config = configparser.RawConfigParser()
    config.read(file_name)
    _LOG.debug("config.sections=%s", config.sections())
    return config


@functools.lru_cache()
def get_aws_credentials(
    aws_profile: str,
) -> Dict[str, Optional[str]]:
    """
    Read the AWS credentials for a given profile.

    :return: a dictionary with `access_key_id`, `aws_secret_access_key`,
        `aws_region` and optionally `aws_session_token`
    """
    dbg.dassert_ne(aws_profile, "")
    _LOG.debug("Getting credentials for aws_profile='%s'", aws_profile)
    result: Dict[str, Optional[str]] = {}
    key_to_env_var: Dict[str, str] = {
        "aws_access_key_id": "AWS_ACCESS_KEY_ID",
        "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
        # TODO(gp): AWS_DEFAULT_REGION -> AWS_REGION?
        "aws_region": "AWS_DEFAULT_REGION",
    }
    # If the AWS credentials are passed through env vars, they override the
    # config file.
    # Check if one env var is defined.
    env_var_override = any(
        (env_var in os.environ and os.environ[env_var] != "")
        for env_var in key_to_env_var.values()
    )
    if env_var_override:
        _LOG.warning("Using AWS credentials from env vars")
        # TODO(gp): Support also other S3 profiles. We can derive the names of the
        #  env vars from aws_profile. E.g., "am" -> AWS_AM_ACCESS_KEY.
        dbg.dassert_eq(aws_profile, "am")
        # If one variable is defined all should be defined.
        for key, env_var in key_to_env_var.items():
            _LOG.debug("'%s' in env vars=%s", env_var, env_var in os.environ)
            _LOG.debug(
                "'%s' != ''=%s", env_var, os.environ.get(env_var, None) != ""
            )
            dbg.dassert_in(env_var, os.environ)
            result[key] = os.environ[env_var]
        # TODO(gp): We don't pass this through env var for now.
        result["aws_session_token"] = None
    else:
        # > more ~/.aws/credentials
        # [am]
        # aws_access_key_id=AKI...
        # aws_secret_access_key=mhg..
        # aws_session_token = Fwo...
        file_name = "credentials"
        config = _get_aws_config(file_name)
        #
        key = "aws_access_key_id"
        result[key] = config.get(aws_profile, key)
        #
        key = "aws_secret_access_key"
        result[key] = config.get(aws_profile, key)
        #
        key = "aws_session_token"
        if config.has_option(aws_profile, key):
            result[key] = config.get(aws_profile, key)
        else:
            result[key] = None
        # > more ~/.aws/config
        # [am]
        # region = us-east-1
        file_name = "config"
        config = _get_aws_config(file_name)
        key = "aws_region"
        result[key] = config.get(aws_profile, "region")
    #
    dbg.dassert_is_subset(key_to_env_var.keys(), result.keys())
    return result


def get_bucket() -> str:
    """
    Return the default s3 bucket.

    Make sure your ~/.aws/credentials uses the right key to access this
    bucket as default.
    """
    env_var = "AM_S3_BUCKET"
    dbg.dassert_in(env_var, os.environ)
    s3_bucket = os.environ[env_var]
    return s3_bucket


# TODO(gp): -> get_bucket_path() ?
def get_path() -> str:
    """
    Return the path corresponding to the default s3 bucket.
    """
    path = "s3://" + get_bucket()
    return path


def is_s3_path(path: str) -> bool:
    return path.startswith("s3://")


# #############################################################################


def get_s3fs(*args: Any, **kwargs: Any) -> s3fs.core.S3FileSystem:
    # From https://stackoverflow.com/questions/62562945
    aws_credentials = get_aws_credentials(*args, **kwargs)
    _LOG.debug("%s", pprint.pformat(aws_credentials))
    s3 = s3fs.core.S3FileSystem(
        anon=False,
        key=aws_credentials["aws_access_key_id"],
        secret=aws_credentials["aws_secret_access_key"],
        token=aws_credentials["aws_session_token"],
        client_kwargs={"region_name": aws_credentials["aws_region"]},
    )
    return s3


# TODO(gp): Replace with `is_s3_path()`.
def is_valid_s3_path(s3_path: str) -> bool:
    return s3_path.startswith("s3://")


def check_valid_s3_path(s3_path: str) -> None:
    dbg.dassert(is_valid_s3_path(s3_path), "Invalid S3 file='%s'", s3_path)
