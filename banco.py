# banco.py - tudo que conversa com o MySQL fica neste arquivo

import mysql.connector
import numpy as np

from config import DB_CONFIG


def conectar():
    return mysql.connector.connect(**DB_CONFIG)


def criar_usuario(nome, perfil="aluno"):
    """Insere uma pessoa e devolve o id dela."""
    con = conectar()
    cur = con.cursor()
    cur.execute("INSERT INTO usuarios (nome, perfil) VALUES (%s, %s)", (nome, perfil))
    con.commit()
    usuario_id = cur.lastrowid
    cur.close()
    con.close()
    return usuario_id


def salvar_encoding(usuario_id, vetor):
    """Guarda o vetor de 128 números do rosto como bytes (BLOB)."""
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO encodings (usuario_id, vetor) VALUES (%s, %s)",
        (usuario_id, vetor.astype(np.float64).tobytes()),
    )
    con.commit()
    cur.close()
    con.close()


def carregar_encodings():
    """Lê todos os rostos de usuários ativos. Devolve três listas paralelas."""
    con = conectar()
    cur = con.cursor()
    cur.execute(
        """SELECT e.usuario_id, u.nome, e.vetor
           FROM encodings e
           JOIN usuarios u ON u.id = e.usuario_id
           WHERE u.ativo = 1"""
    )
    ids, nomes, vetores = [], [], []
    for usuario_id, nome, blob in cur.fetchall():
        ids.append(usuario_id)
        nomes.append(nome)
        vetores.append(np.frombuffer(blob, dtype=np.float64))
    cur.close()
    con.close()
    return ids, nomes, vetores


def registrar_acesso(usuario_id, resultado, distancia):
    """Grava uma tentativa de acesso ('liberado' ou 'negado')."""
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO registros_acesso (usuario_id, resultado, distancia) VALUES (%s, %s, %s)",
        (usuario_id, resultado, distancia),
    )
    con.commit()
    cur.close()
    con.close()


# ---------------------------------------------------------------------------
# Funções usadas pelo painel administrativo (app.py)
# ---------------------------------------------------------------------------

def _consultar(sql, params=()):
    con = conectar()
    cur = con.cursor(dictionary=True)
    cur.execute(sql, params)
    linhas = cur.fetchall()
    cur.close()
    con.close()
    return linhas


def _executar(sql, params=()):
    con = conectar()
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    afetadas = cur.rowcount
    cur.close()
    con.close()
    return afetadas


def listar_usuarios():
    return _consultar(
        """SELECT u.id, u.nome, u.perfil, u.ativo, u.criado_em,
                  (SELECT COUNT(*) FROM encodings e WHERE e.usuario_id = u.id) AS amostras
           FROM usuarios u ORDER BY u.nome"""
    )


def alterar_ativo(usuario_id, ativo):
    return _executar("UPDATE usuarios SET ativo = %s WHERE id = %s", (1 if ativo else 0, usuario_id))


def alterar_perfil(usuario_id, perfil):
    return _executar("UPDATE usuarios SET perfil = %s WHERE id = %s", (perfil, usuario_id))


def excluir_usuario(usuario_id):
    """Apaga a pessoa e os dados faciais dela (encodings caem em cascata).
    Os registros de acesso ficam no histórico, mas sem o vínculo com a pessoa."""
    return _executar("DELETE FROM usuarios WHERE id = %s", (usuario_id,))


def listar_acessos(limite=50):
    return _consultar(
        """SELECT r.id, r.data_hora, r.resultado, r.distancia, u.nome
           FROM registros_acesso r
           LEFT JOIN usuarios u ON u.id = r.usuario_id
           ORDER BY r.data_hora DESC, r.id DESC LIMIT %s""",
        (int(limite),),
    )


def resumo():
    """Números do dia para os cartões do painel."""
    hoje = _consultar(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(resultado = 'liberado'), 0) AS liberados,
                  COALESCE(SUM(resultado = 'negado'), 0) AS negados
           FROM registros_acesso WHERE data_hora >= CURDATE()"""
    )[0]
    ativos = _consultar("SELECT COUNT(*) AS n FROM usuarios WHERE ativo = 1")[0]["n"]
    return {"total": int(hoje["total"]), "liberados": int(hoje["liberados"]),
            "negados": int(hoje["negados"]), "usuarios_ativos": int(ativos)}


# --- administradores do painel (a senha NUNCA é guardada pura, só o hash) ---

def garantir_tabela_admin():
    _executar(
        """CREATE TABLE IF NOT EXISTS administradores (
               id         INT AUTO_INCREMENT PRIMARY KEY,
               usuario    VARCHAR(50)  NOT NULL UNIQUE,
               senha_hash VARCHAR(255) NOT NULL,
               criado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
           )"""
    )


def salvar_admin(usuario, senha_hash):
    garantir_tabela_admin()
    _executar(
        """INSERT INTO administradores (usuario, senha_hash) VALUES (%s, %s)
           ON DUPLICATE KEY UPDATE senha_hash = VALUES(senha_hash)""",
        (usuario, senha_hash),
    )


def obter_admin(usuario):
    linhas = _consultar("SELECT usuario, senha_hash FROM administradores WHERE usuario = %s", (usuario,))
    return linhas[0] if linhas else None
