# coding=utf-8
from __future__ import absolute_import
from peewee import CharField, TextField, IntegerField
from octoprint_qr.models.BaseModel import BaseModel


class QrModel(BaseModel):
    code = CharField()
    gcodeText = TextField(null=True)
    displayName = CharField(null=True)
    spoolManagerId = IntegerField(null=True)
