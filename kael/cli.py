#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
from . import __version__


@click.group()
@click.version_option(__version__)
def cli():
    pass


def main():
    cli()


if __name__ == '__main__':
    main()
