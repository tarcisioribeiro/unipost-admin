"""
Pacote de páginas da aplicação UniPost.

Este pacote contém todas as páginas da aplicação,
organizadas em módulos separados para melhor manutenibilidade.
"""

from .dashboard import Dashboard
from .post_generator import PostGenerator
from .posts_viewer import PostsViewer
from .settings import Settings

__all__ = [
    'Dashboard',
    'PostGenerator', 
    'PostsViewer',
    'Settings'
]