#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="nagios-plugin-graylog2",
    description="A graylog2 availability and performance monitoring plugin for Nagios.",
    version="0.1",
    packages=[],
    author="Peter Adam",
    author_email="info@cygusnetworks.de",
    scripts=["check_graylog2"],
    license="GPL-2",
    install_requires=['nagiosplugin'],
)
