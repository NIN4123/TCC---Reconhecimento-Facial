# Controle de Acesso com Reconhecimento Facial utilizando Inteligência Artificial

Sistema que identifica pessoas pela câmera e libera ou nega o acesso de acordo com as permissões cadastradas. Os dados dos usuários e o histórico de acessos ficam em um banco MySQL, e um painel web permite administrar tudo pelo navegador.

Projeto da disciplina **Projetos Integrados I** do curso de **Análise e Desenvolvimento de Sistemas** da **Universidade de Uberaba** (2026).

## Funcionalidades

- **Cadastro de rosto pela webcam:** captura 5 amostras de cada pessoa e guarda apenas os vetores numéricos do rosto, nunca as fotos.
- **Reconhecimento em tempo real:** compara o rosto da câmera com os cadastrados e decide entre acesso liberado ou negado.
- **Feedback na tela:** faixa verde com cadeado aberto para acesso liberado, vermelha para negado, com som e nome da pessoa.
- **Área restrita:** ao liberar o acesso, o sistema abre uma pasta (ou o painel) que só aparece para quem foi reconhecido. Essa ação fica no `acao.py`, e é o ponto de integração para uma fechadura real no futuro.
- **Histórico de acessos:** cada entrada é registrada no banco, uma vez por passagem (e não a cada quadro da câmera).
- **Painel administrativo web:** login com senha, números do dia, última leitura, lista de usuários (trocar perfil, bloquear, reativar, excluir) e histórico. Atualiza sozinho a cada 3 segundos.
- **Bloqueio imediato:** o reconhecimento relê o banco a cada 5 segundos, então bloquear alguém no painel vale quase na hora.
- **Execução sem terminal:** o `iniciar.pyw` abre uma janela com botões para cadastrar, reconhecer e abrir o painel.

## Fluxogramas

| Cadastro de rosto | Reconhecimento facial |
|---|---|
| ![Fluxograma do cadastro](docs/fluxograma_1_cadastro.png) | ![Fluxograma do reconhecimento](docs/fluxograma_2_reconhecimento.png) |

## Tecnologias

| Para quê | O quê |
|---|---|
| Linguagem | Python 3.11 |
| Visão computacional | OpenCV |
| Reconhecimento facial | face_recognition (dlib) |
| Backend do painel | Flask |
| Banco de dados | MySQL 8 |
| Interface do painel | HTML, CSS e JavaScript |
| Janela inicial | tkinter |
| Versionamento | Git e GitHub |

## Estrutura do projeto

```
.
├── acao.py              # o que acontece ao liberar/negar (cadeado, som, área restrita)
├── app.py               # backend do painel (Flask)
├── banco.py             # todas as operações com o MySQL
├── cadastrar.py         # cadastro de rosto pela webcam
├── reconhecer.py        # reconhecimento em tempo real
├── criar_admin.py       # cria o administrador do painel
├── iniciar.pyw          # janela com botões, sem terminal
├── schema.sql           # criação do banco e das tabelas
├── config.example.py    # modelo de configuração (copie para config.py)
├── requirements.txt     # bibliotecas Python
├── painel/
│   ├── login.html
│   └── painel.html
└── docs/                # fluxogramas
```

## Como instalar

Testado no **Windows 10/11**.

### 1. Pré-requisitos

- **Python 3.11** (python.org). Marque a opção "Add python.exe to PATH" na instalação.
  Versões mais novas do Python podem não ter o `dlib` pré-compilado, o que exigiria instalar o Visual Studio C++.
- **MySQL Server 8** e, de preferência, o MySQL Workbench.
- Uma webcam.

### 2. Baixar o projeto

```
git clone https://github.com/NIN4123/TCC---Reconhecimento-Facial.git
cd TCC---Reconhecimento-Facial
```

### 3. Instalar as bibliotecas

Digite no terminal (dentro da pasta do projeto) os comandos abaixo, um por vez:

```
py -3.11 -m pip install -r requirements.txt
py -3.11 -m pip install face_recognition --no-deps
```

O `face_recognition` é instalado à parte, com `--no-deps`, para o pip não tentar compilar o `dlib` (o `dlib-bin` já traz a versão pronta). Um aviso dizendo que o `dlib` "não está instalado" pode ser ignorado.

### 4. Criar o banco de dados

No MySQL (Workbench ou linha de comando), execute o `schema.sql`:

```
source C:/caminho/do/projeto/schema.sql
```

### 5. Configurar

Copie o modelo e coloque a senha do seu MySQL:

```
copy config.example.py config.py
```

Abra o `config.py` e ajuste `DB_CONFIG`. **Esse arquivo não deve ser enviado ao GitHub** (já está no `.gitignore`).

### 6. Criar o administrador do painel

```
py -3.11 criar_admin.py
```

Informe um usuário e uma senha de pelo menos 8 caracteres. A senha é guardada no banco apenas como hash.

## Como usar

### Pela janela inicial (sem terminal)

Dê duplo clique em `iniciar.pyw`. Na janela:

1. **Abrir painel administrativo:** liga o backend e abre o navegador. Entre com o administrador criado no passo 6.
2. **Cadastrar rosto:** digite o nome, escolha o perfil, olhe para a câmera e aperte **ESPAÇO** 5 vezes, variando um pouco o ângulo da cabeça.
3. **Iniciar reconhecimento:** abre a câmera. Para encerrar, aperte **Q** ou feche a janela.

Se algo falhar, a janela mostra a causa. Os detalhes ficam nos arquivos `saida.log` e `painel.log`.

### Pelo terminal

```
py -3.11 cadastrar.py     # cadastro de rosto
py -3.11 reconhecer.py    # reconhecimento
py -3.11 app.py           # painel em http://127.0.0.1:5000
```

O painel só abre neste computador (`127.0.0.1`). Se a porta 5000 estiver ocupada, defina `PORTA_PAINEL` no `config.py`.

## Configurações

Todas ficam no `config.py` (veja o `config.example.py`). As principais:

| Opção | Para quê |
|---|---|
| `TOLERANCIA` | Rigor do reconhecimento. Menor é mais rígido (padrão 0.5). |
| `ACAO_AO_LIBERAR` | O que abrir ao liberar: `"pasta"`, `"painel"` ou `"nenhuma"`. |
| `SEGUNDOS_RECARREGAR` | De quanto em quanto tempo o reconhecimento relê o banco. |
| `PORTA_PAINEL` | Porta do painel web. |

## Segurança e privacidade

- Rosto é **dado pessoal sensível** pela LGPD. O sistema guarda só o vetor numérico (128 valores) de cada rosto, não a foto.
- O painel exige login, e a senha é armazenada como hash.
- O painel escuta apenas em `127.0.0.1`, então não fica exposto na rede.
- As consultas ao banco usam parâmetros, o que protege contra injeção de SQL.
- Excluir um usuário no painel apaga também os dados faciais dele.
- **Nunca envie o `config.py` ao GitHub.** Ele contém a senha do banco.

## Limitações conhecidas

- O sistema pode ser enganado por uma **foto ou vídeo** exibido na frente da câmera, pois não há detecção de vivacidade.
- O login do painel não bloqueia tentativas erradas repetidas.
- O desbloqueio é simulado no computador (cadeado na tela e área restrita). Não há fechadura física.
- Depende de boa iluminação e de o rosto estar de frente para a câmera.

## Trabalhos futuros

- Detecção de vivacidade (prova de que é uma pessoa real).
- Integração com fechadura ou catraca (Arduino, ESP32 ou Raspberry Pi), trocando apenas o `acao.py`.
- Limite de tentativas de login e proteção contra CSRF no painel.
- Permissões por área e por horário.

## Autores

- Elen Vitória Almeida da Cruz
- Estela Cristina de Almeida Alves
- Miguel Cadelca
- Raissa Freitas Alves

Curso de Análise e Desenvolvimento de Sistemas, Universidade de Uberaba.

## Licença

Projeto acadêmico, desenvolvido para fins educacionais. Defina uma licença (por exemplo, MIT) antes de reutilizar o código em outros contextos.
