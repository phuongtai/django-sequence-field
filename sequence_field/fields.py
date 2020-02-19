# -*- coding: utf-8 -*-

from django.db import models
from sequence_field.models import Sequence
from sequence_field.exceptions import SequenceFieldException
from sequence_field import settings as sequence_field_settings
from sequence_field import strings


class SequenceField(models.TextField):
    """ Stores sequence values based on templates. """

    description = strings.SEQUENCE_FIELD_DESCRIPTION

    def __init__(self, verbose_name=None, key="default_key", template="%NNNNN",
            default=None, name=None, pattern=None, expanders=None,
            params={}, auto=True, **kwargs):

        super().__init__(verbose_name, name, default=default, **kwargs)
        self.default_error_messages = {
            'invalid': strings.SEQUENCE_FIELD_PATTERN_MISMATCH
        }
        self._db_type = kwargs.pop('db_type', None)
        self.evaluate_formfield = kwargs.pop('evaluate_formfield', False)

        self.lazy = kwargs.pop('lazy', True)

        self.key = key

        default_pattern = \
            sequence_field_settings.SEQUENCE_FIELD_DEFAULT_PATTERN
        self.pattern = pattern or default_pattern

        default_template = Sequence.get_template_by_key(self.key)
        self.template = template or default_template

        Sequence.create_if_missing(self.key, self.template)

        default_expanders = \
            sequence_field_settings.SEQUENCE_FIELD_DEFAULT_EXPANDERS

        self.params = params or {}

        self.expanders = expanders or default_expanders

        self.auto = auto

        kwargs['help_text'] = kwargs.get(
            'help_text', self.default_error_messages['invalid']
        )

    def _next_value(self):
        seq = Sequence.create_if_missing(self.key, self.template)
        return seq.next_value(self.template, self.params, self.expanders)

    def pre_save(self, model_instance, add):
        """
        This is used to ensure that we auto-set values if required.
        See CharField.pre_save
        """
        value = getattr(model_instance, self.attname, None)
        if self.auto and add and not value:
            # Assign a new value for this attribute if required.
            sequence_string = self._next_value()
            setattr(model_instance, self.attname, sequence_string)
            value = sequence_string
        return value
