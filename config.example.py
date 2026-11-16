# config.example.py - modelo de configuração.
# Copie este arquivo com o nome config.py e ajuste os valores.
# O config.py NÃO vai para o GitHub (está no .gitignore), porque guarda a senha do banco.

# --- Obrigatório: conexão com o MySQL ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sua_senha",
    "database": "controle_acesso",
}

# --- Câmera e reconhecimento ---
CAMERA_INDEX = 0           # 0 = webcam padrão do computador
TOLERANCIA = 0.5           # quanto menor, mais rígido (0.6 é o padrão da biblioteca)
ESCALA = 0.5               # reduz a imagem para processar mais rápido
AMOSTRAS_CADASTRO = 5      # quantas fotos do rosto são capturadas no cadastro

# --- Opcionais (se não existirem, valem estes valores) ---
# ACAO_AO_LIBERAR = "pasta"      # o que abrir ao liberar: "pasta", "painel" ou "nenhuma"
# SEGUNDOS_STATUS = 4            # tempo que o cadeado fica verde ou vermelho
# INTERVALO_ABRIR = 30           # intervalo mínimo entre aberturas da área restrita
# SEGUNDOS_AUSENCIA = 3          # tempo sem aparecer para contar como "saiu"
# SEGUNDOS_RECARREGAR = 5        # de quanto em quanto tempo relê os rostos do banco
# SOM_ATIVO = True
# PORTA_PAINEL = 5000            # porta do painel (troque se estiver ocupada)
