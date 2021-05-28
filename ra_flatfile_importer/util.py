#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
import hashlib
import json
import sys
from functools import lru_cache
from typing import Any
from typing import Callable
from typing import cast
from typing import TextIO
from typing import Type
from uuid import UUID

import click
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Extra
from pydantic import ValidationError
from pydantic.tools import parse_obj_as


class FrozenBaseModel(BaseModel):
    class Config:
        frozen = True
        extra = Extra.forbid


def load_file_as(model: Type, json_file: TextIO) -> BaseModel:
    json_data = json.load(json_file)
    return cast(BaseModel, model.parse_obj(json_data))


def validate_url(ctx: click.Context, param: Any, value: Any) -> AnyHttpUrl:
    try:
        return cast(AnyHttpUrl, parse_obj_as(AnyHttpUrl, value))
    except ValidationError as e:
        raise click.BadParameter(str(e))


def takes_json_file(function: Callable) -> Callable:
    function = click.option(
        "--json-file",
        help="JSON file of models to parse",
        type=click.File("r"),
        default=sys.stdin,
    )(function)
    return function


def model_validate_helper(model: Type, json_file: TextIO) -> BaseModel:
    try:
        return load_file_as(model, json_file)
    except json.decoder.JSONDecodeError:
        raise click.ClickException("Unable to parse input file as JSON")
    except ValidationError as e:
        raise click.ClickException(str(e))


@lru_cache(maxsize=None)
def generate_uuid(seed: str) -> UUID:
    """
    Generate an UUID based on a seed in a deterministic way
    This allows us generate the same uuid for objects across different imports,
    without having to maintain a separate list of UUIDs, or fetch the relevant uuids
    from MO
    """
    m = hashlib.md5()
    m.update(seed.encode("utf-8"))
    return UUID(m.hexdigest())
