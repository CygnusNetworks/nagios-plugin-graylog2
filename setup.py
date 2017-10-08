#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name="nagios-plugin-graylog2",
	description="A graylog2 availability and performance monitoring plugin for Nagios.",
	version="0.2",
	packages=[],
	author="Peter Adam",
	author_email="info@cygusnetworks.de",
	py_modules=["check_graylog2"],
	entry_points={'console_scripts': ['check_graylog2 = check_graylog2:main']},
	license="GPL-2",
	install_requires=['nagiosplugin'],
)
