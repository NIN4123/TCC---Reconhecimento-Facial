# config.py - todas as configurações do sistema ficam aqui

# Dados de conexão com o MySQL (ajuste usuário e senha)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Almeidaelen123",
    "database": "controle_acesso",
}

CAMERA_INDEX = 0           # 0 = webcam padrão do computador
TOLERANCIA = 0.5           # quanto menor, mais rígido (0.6 é o padrão da biblioteca)
ESCALA = 0.5               # reduz a imagem para processar mais rápido
INTERVALO_REGISTRO = 5     # segundos entre registros da mesma pessoa (evita log repetido)
AMOSTRAS_CADASTRO = 5      # quantas fotos do rosto são capturadas no cadastro
ACAO_AO_LIBERAR = "pasta"      # "pasta", "painel" (abre o painel.html) ou "nenhuma"
SEGUNDOS_STATUS = 4            # quanto tempo o cadeado fica verde ou vermelho
SEGUNDOS_AUSENCIA = 3          # tempo sem aparecer para contar como "saiu"
SOM_ATIVO = True
PORTA_PAINEL = 5001