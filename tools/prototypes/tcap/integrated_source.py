"""Compatibility entry point for the production combined-display source builder."""
from build_integrated_display import source


def display_source(personality='adm3a',backend='crt'):
    return source(personality,backend)
