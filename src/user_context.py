"""Contexto temporário do usuário atual.

Enquanto o FinanTec não possui autenticação, a aplicação trabalha com
um usuário local fixo. Futuramente, este identificador será obtido da
sessão autenticada.
"""

from __future__ import annotations


LOCAL_USER_ID = "local-user"


def get_current_user_id() -> str:
    """Retorna o identificador do usuário ativo."""
    return LOCAL_USER_ID