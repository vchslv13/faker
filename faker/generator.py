# coding=utf-8

from __future__ import unicode_literals

import re
import random as random_module

_re_token = re.compile(r'\{\{(\s?)(\w+)(\s?)\}\}')
random = random_module.Random()
mod_random = random  # compat with name released in 0.8


class Generator(object):

    __config = {}

    def __init__(self, **config):
        self.providers = []
        self.__config = dict(
            list(self.__config.items()) + list(config.items()))
        self.__random = random
        self.context = None

    def add_provider(self, provider):

        if isinstance(provider, type):
            provider = provider(self)

        self.providers.insert(0, provider)

        for method_name in dir(provider):
            # skip 'private' method
            if method_name.startswith('_'):
                continue

            faker_function = getattr(provider, method_name)

            if callable(faker_function):
                # add all faker method to generator
                self.set_formatter(method_name, faker_function)

    def provider(self, name):
        try:
            lst = [p for p in self.get_providers()
                   if p.__provider__ == name.lower()]
            return lst[0]
        except IndexError:
            return None

    def get_providers(self):
        """Returns added providers."""
        return self.providers

    @property
    def random(self):
        return self.__random

    def seed_instance(self, seed=None):
        """Calls random.seed"""
        if self.__random == random:
            # create per-instance random obj when first time seed_instance() is
            # called
            self.__random = random_module.Random()
        self.__random.seed(seed)
        return self

    @classmethod
    def seed(cls, seed=None):
        random.seed(seed)

    def format(self, formatter, *args, **kwargs):
        """
        This is a secure way to make a fake from another Provider.
        """
        formatter_func = self.get_formatter(formatter)
        result = formatter_func(*args, **kwargs)

        if self.context is not None:
            self.context[formatter] = result

            # handle recursive formatters
            if hasattr(result, 'parts'):
                self.context.update(result.parts)

        return result

    def get_formatter(self, formatter):
        try:
            return getattr(self, formatter)
        except AttributeError:
            if 'locale' in self.__config:
                msg = 'Unknown formatter "{0}" with locale "{1}"'.format(
                    formatter, self.__config['locale'],
                )
            else:
                raise AttributeError('Unknown formatter "{0}"'.format(
                    formatter,
                ))
            raise AttributeError(msg)

    def set_formatter(self, name, method):
        """
        This method adds a provider method to generator.
        Override this method to add some decoration or logging stuff.
        """
        setattr(self, name, method)

    def parse(self, text):
        """
        Replaces tokens (like '{{ tokenName }}' or '{{tokenName}}')
        with the result from the token method call.
        """
        is_root_call = False
        if self.context is None:
            self.context = dict()
            is_root_call = True

        str_res = _re_token.sub(self.__format_token, text)
        res = ExtStr(str_res)
        res.parts = self.context

        if is_root_call:
            self.context = None

        return res

    def __format_token(self, matches):
        formatter = list(matches.groups())
        formatter[1] = self.format(formatter[1])
        return ''.join(formatter)


class ExtStr(str):
    pass
