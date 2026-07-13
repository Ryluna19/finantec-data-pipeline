"""Contexto temporário do usuário atual.

Enquanto o FinanTec não possui autenticação, a aplicação trabalha com
um usuário local fixo. Futuramente, o identificador virá da sessão
autenticada.
"""

from __future__ import annotations


LOCAL_USER_ID = "local-user"