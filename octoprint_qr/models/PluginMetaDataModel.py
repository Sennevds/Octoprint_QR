# coding=utf-8
from __future__ import absolute_import

from octoprint_qr.models.BaseModel import BaseModel
from peewee import CharField


class PluginMetaDataModel(BaseModel):

    KEY_PLUGIN_VERSION = "pluginVersion"
    KEY_DATABASE_SCHEME_VERSION = "databaseSchemeVersion"

    key = CharField(null=False)