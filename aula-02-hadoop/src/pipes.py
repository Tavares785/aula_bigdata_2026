"""
Shim mínimo do módulo `pipes` para compatibilidade com Python 3.13+

O pacote `mrjob` ainda tenta importar o módulo padrão `pipes`, removido
em versões recentes do Python. Como os testes adicionam `src/` no início
de `sys.path`, podemos fornecer aqui uma implementação mínima que
expõe `quote()` usando `shlex.quote`.
"""
from __future__ import annotations

import shlex


def quote(s: str) -> str:
    """Retorna uma versão escapada de *s* para uso em linhas de comando.

    Usa `shlex.quote` do stdlib para comportamento seguro em shells POSIX.
    """
    return shlex.quote(s)
