# Arquitetura - Ferramenta de Exploração Android MP4

## Visão Geral

A ferramenta é composta por 4 módulos principais que trabalham em conjunto para gerar arquivos MP4 maliciosos com payload injetado.

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface                         │
│              (main.py / cli_interface.py)                │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──────┐ ┌──▼──────┐ ┌───▼──────┐
│ Payload  │ │  MP4    │ │ Config   │
│Generator │ │ Injector│ │Manager   │
└──────────┘ └─────────┘ └──────────┘
    │            │            │
    └────────────┼────────────┘
                 │
         ┌───────▼────────┐
         │  Output: MP4   │
         │   Malicioso    │
         └────────────────┘
```

## Módulos

### 1. **payload_generator.py**
Responsável pela geração do shellcode ARM64 que será injetado no arquivo MP4.

**Funcionalidades:**
- Gera shellcode ARM64 para diferentes versões do Android
- Suporta diferentes métodos de execução (UAF, ROP)
- Permite customização de URL de download do payload
- Implementa NOP sled para garantir execução
- Suporta ofuscação básica do shellcode

**Estrutura de Classe:**
```python
class PayloadGenerator:
    def __init__(self, target_version, download_url)
    def generate_arm64_shellcode()
    def generate_rop_chain()
    def add_nop_sled()
    def obfuscate_shellcode()
    def get_payload_bytes()
```

### 2. **mp4_injector.py**
Manipula arquivos MP4 para injetar o exploit de forma furtiva.

**Funcionalidades:**
- Parse de estrutura MP4 (atoms/boxes)
- Injeção de payload após metadados
- Preservação de validade do arquivo MP4
- Geração de thumbnail válida
- Ofuscação de estrutura MP4

**Estrutura de Classe:**
```python
class MP4Injector:
    def __init__(self, mp4_file_path)
    def parse_mp4_structure()
    def inject_payload(payload_bytes, offset)
    def inject_after_metadata()
    def preserve_mp4_validity()
    def generate_valid_thumbnail()
    def save_malicious_mp4(output_path)
```

### 3. **config_manager.py**
Gerencia configurações e parâmetros da ferramenta.

**Funcionalidades:**
- Carregamento de configurações padrão
- Validação de parâmetros
- Suporte a arquivos de configuração JSON/YAML
- Gerenciamento de URLs de servidor
- Configurações de ofuscação

### 4. **cli_interface.py**
Interface de linha de comando para automação da ferramenta.

**Funcionalidades:**
- Argumentos de linha de comando (argparse)
- Modo interativo
- Modo batch (múltiplos arquivos)
- Logging detalhado
- Validação de entrada

## Fluxo de Execução

```
1. Usuário executa: python main.py --mp4 video.mp4 --url http://server.com/payload.apk
2. CLI valida parâmetros
3. PayloadGenerator cria shellcode ARM64
4. MP4Injector carrega o arquivo MP4
5. Payload é injetado após metadados
6. Arquivo é salvo como output_malicious.mp4
7. Relatório de sucesso é exibido
```

## Estrutura de Diretórios

```
android-exploit-tooling/
├── main.py                 # Ponto de entrada
├── cli_interface.py        # Interface CLI
├── payload_generator.py    # Gerador de shellcode
├── mp4_injector.py         # Injetor de MP4
├── config_manager.py       # Gerenciador de config
├── utils.py                # Funções utilitárias
├── requirements.txt        # Dependências
├── config/
│   ├── default_config.json # Configuração padrão
│   └── android_versions.json # Dados de versões Android
├── templates/
│   ├── shellcode_templates/ # Templates de shellcode
│   └── rop_gadgets/        # Catálogo de ROP gadgets
├── output/                 # Arquivos gerados
└── docs/
    ├── ARCHITECTURE.md     # Este arquivo
    ├── USAGE.md            # Guia de uso
    └── TECHNICAL.md        # Detalhes técnicos
```

## Dependências Externas

- **struct**: Manipulação de dados binários
- **ctypes**: Tipos C para ARM64
- **pycryptodome**: Ofuscação/criptografia
- **click**: Interface CLI (alternativa a argparse)
- **colorama**: Saída colorida no terminal

## Fluxo de Dados

```
MP4 Original
    │
    ├─→ Parsing de Atoms
    │
    ├─→ Identificação de Metadados
    │
    ├─→ Geração de Shellcode ARM64
    │
    ├─→ Injeção de Payload
    │
    ├─→ Ajuste de Offsets
    │
    └─→ MP4 Malicioso (Output)
```

## Considerações de Segurança

- O shellcode é ofuscado para evitar detecção estática
- O arquivo MP4 mantém validade para enganar verificações superficiais
- Nenhuma string de C&C é deixada em claro no arquivo
- Timestamps são preservados para parecer legítimo

## Próximas Fases

1. Implementação do gerador de shellcode
2. Implementação do injetor MP4
3. Testes com diferentes versões de Android
4. Interface GUI (PyQt5)
5. Ofuscação avançada
