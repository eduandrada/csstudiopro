#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CSStudioPro - MONITOR DE SERVIDORES (A2S QUERY) Y CONSOLA RCON NATIVA
=============================================================================
Implementación nativa en Python con sockets UDP sin dependencias externas:
 1. Protocolo Valve A2S_INFO (Header 0x54) con manejo de challenge (Header 0x41).
 2. Decodificación de nombres, mapa actual, jugadores, VAC y RTT (ping en ms).
 3. Mini-Consola RCON para envío de comandos de administración remota por UDP.
=============================================================================
"""

import socket
import struct
import time
from typing import Dict, Any, Optional, Tuple

from utils.logger import logger

class A2SClient:
    """Cliente de consulta UDP para servidores de Counter-Strike 1.6 (GoldSrc)."""

    A2S_INFO_HEADER = b"\xFF\xFF\xFF\xFF\x54Source Engine Query\x00"

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    def query_server(self, host: str, port: int = 27015) -> Dict[str, Any]:
        """
        Consulta el estado de un servidor CS 1.6 mediante protocolo Valve A2S_INFO.
        Retorna mapa, jugadores, nombre del servidor, ping real y protección VAC.
        """
        result = {
            "online": False,
            "host": host,
            "port": port,
            "name": None,
            "map": None,
            "players": 0,
            "max_players": 0,
            "bots": 0,
            "password": False,
            "vac": False,
            "ping_ms": 999.0,
            "protocol": None,
            "server_type": None,
            "os": None,
            "error": None
        }

        try:
            ip = socket.gethostbyname(host)
        except Exception as e:
            result["error"] = f"No se pudo resolver host: {str(e)}"
            return result

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)

        start_time = time.time()
        try:
            # 1. Enviar consulta A2S_INFO inicial
            sock.sendto(self.A2S_INFO_HEADER, (ip, port))
            data, _ = sock.recvfrom(4096)
            rtt_ms = round((time.time() - start_time) * 1000.0, 1)

            # 2. Verificar si el servidor requiere desafío (Challenge response 0x41)
            if len(data) >= 9 and data[:5] == b"\xFF\xFF\xFF\xFF\x41":
                challenge = data[5:9]
                # Reenviar consulta anexando el número de desafío
                start_time = time.time()
                sock.sendto(self.A2S_INFO_HEADER + challenge, (ip, port))
                data, _ = sock.recvfrom(4096)
                rtt_ms = round((time.time() - start_time) * 1000.0, 1)

            result["ping_ms"] = rtt_ms
            # 3. Parsear respuesta (Header 0x49: Source/Modern GoldSrc, o 0x6D: GoldSrc clásico)
            if len(data) >= 5 and data[:4] == b"\xFF\xFF\xFF\xFF":
                header_byte = data[4]
                if header_byte == 0x49:
                    self._parse_response_0x49(data[5:], result)
                elif header_byte == 0x6D:
                    self._parse_response_0x6D(data[5:], result)
                else:
                    result["error"] = f"Cabecera desconocida: 0x{header_byte:02X}"
                    return result

                result["online"] = True

        except socket.timeout:
            result["error"] = "Tiempo de espera agotado (servidor sin respuesta)."
        except Exception as e:
            result["error"] = str(e)
        finally:
            sock.close()

        return result

    def _read_cstring(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Lee una cadena terminada en null byte de los bytes recibidos."""
        end = data.find(b"\x00", offset)
        if end == -1:
            return "", len(data)
        try:
            text = data[offset:end].decode("utf-8")
        except UnicodeDecodeError:
            text = data[offset:end].decode("cp1252", errors="ignore")
        return text, end + 1

    def _parse_response_0x49(self, payload: bytes, result: Dict[str, Any]):
        """Parsea la respuesta moderna A2S_INFO (Header 0x49)."""
        offset = 0
        if len(payload) < 5:
            return

        result["protocol"] = payload[offset]
        offset += 1

        result["name"], offset = self._read_cstring(payload, offset)
        result["map"], offset = self._read_cstring(payload, offset)
        folder, offset = self._read_cstring(payload, offset)
        game, offset = self._read_cstring(payload, offset)

        if offset + 7 <= len(payload):
            # ID de Steam (short)
            offset += 2
            result["players"] = payload[offset]
            result["max_players"] = payload[offset + 1]
            result["bots"] = payload[offset + 2]
            server_type_char = chr(payload[offset + 3])
            result["server_type"] = "Dedicado" if server_type_char == 'd' else "Listen"
            os_char = chr(payload[offset + 4])
            result["os"] = "Windows" if os_char == 'w' else "Linux"
            result["password"] = bool(payload[offset + 5])
            result["vac"] = bool(payload[offset + 6])

    def _parse_response_0x6D(self, payload: bytes, result: Dict[str, Any]):
        """Parsea la respuesta clásica GoldSrc A2S_INFO (Header 0x6D)."""
        offset = 0
        addr, offset = self._read_cstring(payload, offset)
        result["name"], offset = self._read_cstring(payload, offset)
        result["map"], offset = self._read_cstring(payload, offset)
        folder, offset = self._read_cstring(payload, offset)
        game, offset = self._read_cstring(payload, offset)

        if offset + 5 <= len(payload):
            result["players"] = payload[offset]
            result["max_players"] = payload[offset + 1]
            result["protocol"] = payload[offset + 2]
            result["server_type"] = "Dedicado" if chr(payload[offset + 3]) == 'd' else "Listen"
            result["os"] = "Windows" if chr(payload[offset + 4]) == 'w' else "Linux"
            offset += 5
            if offset < len(payload):
                result["password"] = bool(payload[offset])


class RCONClient:
    """Cliente RCON para envío de comandos de administración remota a servidores GoldSrc."""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout

    def send_command(self, host: str, port: int, rcon_password: str, command: str) -> Dict[str, Any]:
        """
        Ejecuta un comando RCON contra un servidor de Counter-Strike 1.6 vía UDP.
        """
        result = {"success": False, "response": "", "error": None}

        try:
            ip = socket.gethostbyname(host)
        except Exception as e:
            result["error"] = f"No se pudo resolver el host: {e}"
            return result

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)

        try:
            # 1. Solicitar desafío de RCON (challenge rcon)
            sock.sendto(b"\xFF\xFF\xFF\xFFchallenge rcon\n", (ip, port))
            data, _ = sock.recvfrom(2048)

            # La respuesta viene en formato: \xFF\xFF\xFF\xFFchallenge rcon 123456789\n
            text_resp = data.decode("latin-1", errors="ignore")
            parts = text_resp.strip().split()
            challenge = None
            for p in parts:
                if p.isdigit():
                    challenge = p
                    break

            if not challenge:
                challenge = "0"

            # 2. Enviar el comando autenticado con el challenge obtenido
            rcon_packet = f'\xFF\xFF\xFF\xFFrcon {challenge} "{rcon_password}" {command}\n'.encode("latin-1")
            sock.sendto(rcon_packet, (ip, port))

            # Recibir salida del comando
            output_parts = []
            try:
                while True:
                    data, _ = sock.recvfrom(4096)
                    cleaned = data.replace(b"\xFF\xFF\xFF\xFFl", b"").replace(b"\xFF\xFF\xFF\xFF", b"")
                    output_parts.append(cleaned.decode("latin-1", errors="ignore"))
            except socket.timeout:
                pass

            out_text = "".join(output_parts).strip()
            result["success"] = True
            result["response"] = out_text or "(Comando ejecutado sin salida en consola)"
            logger.info(f"[RCON] Comando '{command}' enviado a {host}:{port}")

        except socket.timeout:
            result["error"] = "Tiempo de espera agotado al conectar con RCON."
        except Exception as e:
            result["error"] = str(e)
        finally:
            sock.close()

        return result


# Instancias singleton
a2s_client = A2SClient()
rcon_client = RCONClient()
