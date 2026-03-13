"""
api.py - Cliente principal para WhaticketAPI
Maneja la conexión y operaciones con el sistema de tickets
"""

import requests
import json
from typing import List, Dict, Optional, Any, Union

class WhaticketClient:
    """
    Cliente principal para interactuar con Whaticket
    """
    
    def __init__(self, base_url: str, token: str):
        """
        Inicializa el cliente con URL base y token
        
        Args:
            base_url: URL base de la API (ej: https://app.whaticket.com)
            token: Token de autenticación Bearer
        """
        self.base_url = base_url.rstrip('/')
        self.token = self._limpiar_token(token)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _limpiar_token(self, token: str) -> str:
        """Limpia el token de comillas y espacios"""
        return token.strip().replace('"', '').replace("'", "")
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Any:
        """
        Método interno para hacer peticiones HTTP
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Endpoint relativo (ej: /users)
            params: Parámetros de query string
            data: Datos para body en POST/PUT
        
        Returns:
            Respuesta parseada de la API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise Exception("Error 401: Token inválido o expirado")
            elif response.status_code == 404:
                raise Exception(f"Error 404: Endpoint no encontrado: {endpoint}")
            else:
                raise Exception(f"Error {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            raise Exception(f"Error de conexión: No se pudo conectar a {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("Timeout: La petición tardó demasiado")
        except Exception as e:
            raise Exception(f"Error en la petición: {str(e)}")
    
    # ==================== MÉTODOS DE AUTENTICACIÓN Y DESCUBRIMIENTO ====================
    
    def validate_token(self) -> bool:
        """
        Valida que el token sea correcto intentando obtener usuarios
        
        Returns:
            True si el token es válido
        """
        try:
            self._request("GET", "/users", params={"pageNumber": 1, "pageSize": 1})
            return True
        except:
            return False
    
    def get_users(self) -> List[Dict]:
        """
        Obtiene todos los usuarios del sistema
        
        Returns:
            Lista de objetos usuario [{id, name, email, ...}]
        """
        response = self._request("GET", "/users", params={"pageNumber": 1, "pageSize": 100})
        
        # Manejar diferentes formatos de respuesta
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            return response.get("users", response.get("data", []))
        return []
    
    def get_queues(self) -> List[Dict]:
        """
        Obtiene todas las colas disponibles
        
        Returns:
            Lista de objetos cola [{id, name, ...}]
        """
        response = self._request("GET", "/queue")
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            return response.get("queues", response.get("data", []))
        return []
    
    def get_tags(self) -> List[Dict]:
        """
        Obtiene todos los tags disponibles
        
        Returns:
            Lista de objetos tag [{id, name, color, ...}]
        """
        # Intentar diferentes endpoints para tags
        endpoints = ["/tags", "/tag", "/tags?pageNumber=1"]
        
        for endpoint in endpoints:
            try:
                response = self._request("GET", endpoint)
                if isinstance(response, list):
                    return response
                elif isinstance(response, dict):
                    tags = response.get("tags", response.get("data", []))
                    if tags:
                        return tags
            except:
                continue
        
        return []
    
    # ==================== MÉTODOS DE TICKETS ====================
    
    def search_tickets(self, queue_ids=None, status="open", page=1, 
                   search_param="", show_all=True,
                   without_tag=False, without_queue=False, without_connection=False,
                   users_ids=None, tags_ids=None, connections_ids=None,
                   channels=None):
        """
        Busca tickets con todos los filtros que usa Whaticket
        
        Args:
            queue_ids: Lista de IDs de colas (ej: ["id1", "id2"] o None para todas)
            status: "open" o "pending" (se formateará automáticamente con comillas)
            page: Número de página
            search_param: Texto de búsqueda
            show_all: Mostrar todos los tickets
            without_tag: Excluir con tags
            without_queue: Excluir sin cola
            without_connection: Excluir sin conexión
            users_ids: Lista de IDs de usuarios
            tags_ids: Lista de IDs de tags
            connections_ids: Lista de IDs de conexiones
            channels: Lista de canales (por defecto todos)
        """
        
        # Valores por defecto
        if channels is None:
            channels = ["FACEBOOK", "INSTAGRAM", "WHATSAPP", "WIDGET", "WABA", "TIKTOK"]
        
        if queue_ids is None:
            queue_ids = []
        
        if users_ids is None:
            users_ids = []
        
        if tags_ids is None:
            tags_ids = []
        
        if connections_ids is None:
            connections_ids = []
        
        # Construir parámetros exactamente como en el fetch
        params = {
            "searchParam": search_param,
            "pageNumber": page,
            "status": f'"{status}"',  # ¡Importante! con comillas dobles
            "showAll": str(show_all).lower(),
            "withUnreadMessages": "false",  # Siempre false, solo controla si incluye el contador
            "withoutTag": str(without_tag).lower(),
            "withoutQueue": str(without_queue).lower(),
            "withoutConnection": str(without_connection).lower(),
            "queueIds": json.dumps(queue_ids),
            "connectionsIds": json.dumps(connections_ids),
            "tagsIds": json.dumps(tags_ids),
            "usersIds": json.dumps(users_ids),
            "channels": json.dumps(channels)
        }
        
        response = self._request("GET", "/tickets", params=params)
        
        # La respuesta viene como {"tickets": [...]}
        if isinstance(response, dict):
            return response.get("tickets", [])
        return response
    
    def get_ticket(self, ticket_id: Union[int, str]) -> Dict:
        """
        Obtiene un ticket específico por ID
        
        Args:
            ticket_id: ID del ticket
        
        Returns:
            Objeto ticket con todos sus detalles
        """
        return self._request("GET", f"/tickets/{ticket_id}")
    
    def get_ticket_messages(self, ticket_id: Union[int, str], limit: int = 50) -> List[Dict]:
        """
        Obtiene los mensajes de un ticket
        
        Args:
            ticket_id: ID del ticket
            limit: Número máximo de mensajes
        
        Returns:
            Lista de mensajes del ticket
        """
        params = {"pageSize": limit}
        response = self._request("GET", f"/tickets/{ticket_id}/messages", params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            return response.get("messages", response.get("data", []))
        return []
    
    # ==================== MÉTODOS DE MENSAJES ====================
    
    def send_message(self, ticket_id: Union[int, str], message: str) -> Dict:
        """
        Envía un mensaje simple a un ticket
        
        Args:
            ticket_id: ID del ticket destino
            message: Contenido del mensaje
        
        Returns:
            {success: bool, message_id: str, timestamp: str}
        """
        data = {
            "body": message,
            "ticketId": ticket_id
        }
        
        try:
            response = self._request("POST", "/messages", data=data)
            return {
                "success": True,
                "message_id": response.get("id", ""),
                "timestamp": response.get("createdAt", ""),
                "data": response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_template(self, ticket_id: Union[int, str], template_name: str, 
                     parameters: Dict[str, str] = None) -> Dict:
        """
        Envía un mensaje usando plantilla predefinida
        
        Args:
            ticket_id: ID del ticket destino
            template_name: Nombre de la plantilla
            parameters: Variables para la plantilla
        
        Returns:
            {success: bool, message_id: str, rendered_body: str}
        """
        # Primero obtener la plantilla
        templates = self._request("GET", "/templates")
        
        template = None
        if isinstance(templates, list):
            for t in templates:
                if t.get("name") == template_name:
                    template = t
                    break
        
        if not template:
            return {
                "success": False,
                "error": f"Plantilla '{template_name}' no encontrada"
            }
        
        # Renderizar plantilla con parámetros
        body = template.get("body", "")
        if parameters:
            for key, value in parameters.items():
                body = body.replace(f"{{{{{key}}}}}", value)
                body = body.replace(f"{{{key}}}", value)
        
        # Enviar mensaje renderizado
        return self.send_message(ticket_id, body)
    
    def send_media(self, ticket_id: Union[int, str], media_url: str, 
                  caption: str = None) -> Dict:
        """
        Envía un mensaje con archivo multimedia
        
        Args:
            ticket_id: ID del ticket destino
            media_url: URL del archivo
            caption: Texto opcional
        
        Returns:
            {success: bool, media_id: str}
        """
        data = {
            "ticketId": ticket_id,
            "mediaUrl": media_url
        }
        
        if caption:
            data["caption"] = caption
        
        try:
            response = self._request("POST", "/messages/media", data=data)
            return {
                "success": True,
                "media_id": response.get("id", ""),
                "data": response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }