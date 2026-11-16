# criar_admin.py - cria (ou troca a senha de) um administrador do painel
# Uso: py -3.11 criar_admin.py

import getpass

from werkzeug.security import generate_password_hash

import banco


def main():
    usuario = input("Nome de usuário do administrador: ").strip()
    senha = getpass.getpass("Senha (mínimo 8 caracteres): ")
    if not usuario or len(senha) < 8:
        print("Usuário obrigatório e senha com pelo menos 8 caracteres.")
        return
    if senha != getpass.getpass("Repita a senha: "):
        print("As senhas não conferem.")
        return
    banco.salvar_admin(usuario, generate_password_hash(senha))
    print(f"Administrador '{usuario}' salvo com sucesso.")


if __name__ == "__main__":
    main()
