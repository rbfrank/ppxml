"""
Core infrastructure for TEI conversion.

This package contains the foundational components for converting TEI XML
to various output formats using a visitor pattern with context management.
"""

from .context import RenderContext
from .traverser import TEITraverser
from .base_renderer import BaseRenderer

__all__ = ['RenderContext', 'TEITraverser', 'BaseRenderer']
