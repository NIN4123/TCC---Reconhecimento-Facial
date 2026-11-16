-- schema.sql - execute uma vez no MySQL (Workbench ou linha de comando)

CREATE DATABASE IF NOT EXISTS controle_acesso
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE controle_acesso;

-- Pessoas cadastradas e o que elas podem fazer
CREATE TABLE IF NOT EXISTS usuarios (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    nome       VARCHAR(120) NOT NULL,
    perfil     VARCHAR(30)  NOT NULL DEFAULT 'aluno',
    ativo      TINYINT(1)   NOT NULL DEFAULT 1,   -- 0 = acesso bloqueado
    criado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Vetores faciais (128 números por foto). Uma pessoa pode ter várias amostras.
CREATE TABLE IF NOT EXISTS encodings (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT NOT NULL,
    vetor       BLOB NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Histórico de tentativas de acesso
CREATE TABLE IF NOT EXISTS registros_acesso (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT NULL,                          -- NULL = rosto desconhecido
    data_hora   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resultado   ENUM('liberado', 'negado') NOT NULL,
    distancia   FLOAT NULL,                        -- quão parecido o rosto foi (menor = mais parecido)
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- Administradores do painel web (criados pelo script criar_admin.py)
CREATE TABLE IF NOT EXISTS administradores (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario     VARCHAR(50)  NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,                -- hash da senha, nunca a senha pura
    criado_em   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
