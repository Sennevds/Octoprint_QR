# -*- coding: utf-8 -*-
from __future__ import absolute_import

from peewee import CharField

from octoprint_qr.models.BaseModel import BaseModel


class PluginMetaDataModel(BaseModel):

    KEY_PLUGIN_VERSION = "pluginVersion"
    KEY_DATABASE_SCHEME_VERSION = "databaseSchemeVersion"

    key = CharField(null=False)
