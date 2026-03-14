"""
api.py - Cliente principal para WhaticketAPI
Maneja la conexión y operaciones con el sistema de tickets
"""

import requests
import json
from typing import List, Dict, Optional, Any, Union, BinaryIO

import hashlib
import uuid
from PIL import Image
from pathlib import Path

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
            
            if response.status_code in [200,201]:
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
    
    def transfer_ticket(self, ticket_id: Union[int, str], user_id: str, queue_id: str = None) -> Dict:
        """
        [FUNCIÓN 3] Transfiere un ticket a otro usuario
        
        Args:
            ticket_id: ID del ticket a transferir
            user_id: ID del usuario destino
            queue_id: ID de la cola destino (opcional)
        
        Returns:
            {"success": bool, "data": dict, "new_user": str, "old_user": str}
        """
        url = f"/tickets/{ticket_id}/transfer"
        
        # Payload exactamente como en la petición que capturaste
        payload = {"userId": user_id}
        if queue_id:
            payload["queueId"] = queue_id
        
        try:
            response = self._request("POST", url, data=payload)
            return {
                "success": True,
                "data": response,
                "new_user": response.get("newUserName"),
                "old_user": response.get("oldUserName")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


    def get_fast_responses(self) -> List[Dict]:
        """
        Obtiene todas las respuestas rápidas
        """
        response = self._request("GET", "/fastresponse")
        
        if isinstance(response, dict):
            return response.get("fastResponses", [])
        return response if isinstance(response, list) else []


    def send_fast_response_by_id(self, ticket_id: Union[int, str], fast_response_id: str, contact_name: str = None) -> Dict:
        """
        Envía una respuesta rápida por su ID
        """
        # Obtener todas
        all_responses = self.get_fast_responses()
        
        # Buscar la que necesitas
        selected = None
        for fr in all_responses:
            if fr.get("id") == fast_response_id:
                selected = fr
                break
        
        if not selected:
            return {"success": False, "error": "ID no encontrado"}
        
        # Preparar mensaje
        message = selected.get("message", "")
        if contact_name:
            message = message.replace("{{contactName}}", contact_name)
        
        # Enviar
        return self.send_message(ticket_id, message)


    def send_fast_response_by_shortcut(self, ticket_id: Union[int, str], shortcut: str, contact_name: str = None) -> Dict:
        """
        Envía una respuesta rápida buscándola por su shortcut (nombre)
        
        Args:
            ticket_id: ID del ticket destino
            shortcut: El nombre/shortcut de la respuesta (ej: "01", "AVISO1", "RESERVA S/5")
            contact_name: Nombre del contacto (para reemplazar {{contactName}})
        
        Returns:
            Resultado del envío
        """
        # 1. Obtener todas las respuestas (esto llama a la API)
        all_responses = self.get_fast_responses()
        
        # 2. Buscar por shortcut (nombre)
        selected = None
        for fr in all_responses:
            if fr.get("shortcut", "").lower() == shortcut.lower():
                selected = fr
                break
        
        if not selected:
            return {
                "success": False, 
                "error": f"Respuesta rápida '{shortcut}' no encontrada"
            }
        
        # 3. Preparar mensaje
        message = selected.get("message", "")
        if contact_name and message:
            message = message.replace("{{contactName}}", contact_name)
        
        # 4. Enviar
        return self.send_message(ticket_id, message)
    
    def get_contact_name_from_ticket(self, ticket_id: Union[int, str]) -> str:
        """
        Obtiene el nombre del contacto de un ticket
        
        Args:
            ticket_id: ID del ticket
        
        Returns:
            Nombre del contacto o "Cliente" si no se encuentra
        """
        try:
            ticket = self.get_ticket(ticket_id)
            
            # Buscar en diferentes lugares donde puede estar el contacto
            contact = ticket.get('contact', {})
            if not contact and 'ticket' in ticket:
                contact = ticket['ticket'].get('contact', {})
            
            name = contact.get('name', '')
            if name:
                return name
            
            # Si no hay nombre, intentar con el número
            phone = contact.get('number', '')
            if phone:
                return f"Cliente {phone[-4:]}"  # Últimos 4 dígitos
            
            return "Cliente"
            
        except Exception as e:
            print(f"Error obteniendo nombre: {e}")
            return "Cliente"
    def get_contact(self, contact_id: str) -> Dict:
        """
        Obtiene un contacto por su ID
        """
        return self._request("GET", f"/contacts/{contact_id}")


    def get_contact_extra_info(self, contact_id: str) -> List[Dict]:
        """
        Obtiene solo los campos extra de un contacto
        """
        contact = self.get_contact(contact_id)
        return contact.get("extraInfo", [])

    def add_contact_extra_field(self, contact_id: str, field_name: str, field_value: str) -> Dict:
        """
        AGREGA un campo extra al contacto SIN borrar los existentes
        """
        # 1. Obtener contacto ACTUAL
        current_contact = self.get_contact(contact_id)
        
        # 2. Obtener extraInfo existente
        extra_info = current_contact.get("extraInfo", [])
        
        # 3. AGREGAR el nuevo campo
        extra_info.append({
            "name": field_name,
            "value": field_value
        })
        
        # 4. Actualizar
        current_contact["extraInfo"] = extra_info
        
        # 5. Enviar PUT
        return self._request("PUT", f"/contacts/{contact_id}", data=current_contact)

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
            "body": message
        }
        
        try:
            response = self._request("POST", f"/messages/{ticket_id}", data=data)
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
    
    def send_image(self, ticket_id: Union[int, str], image_path: str, company_id: str = None) -> Dict:
        """
        Envía una imagen a un ticket específico
        
        Args:
            ticket_id: ID del ticket destino
            image_path: Ruta local de la imagen
            company_id: ID de la compañía (opcional)
        
        Returns:
            Dict con resultado del envío
        """
        try:
            from pathlib import Path
            import hashlib
            import uuid
            from PIL import Image
            import requests

            # Validar que el archivo existe
            if not Path(image_path).exists():
                return {"success": False, "error": f"Archivo no encontrado: {image_path}"}

            # 1️⃣ Leer archivo y calcular hash
            with open(image_path, "rb") as f:
                file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            filename = Path(image_path).name
            
            # Detectar content type (simple, puedes mejorarlo)
            if filename.lower().endswith('.png'):
                content_type = "image/png"
            else:
                content_type = "image/jpeg"

            print(f"📤 Solicitando URL de subida para {filename}...")

            # 2️⃣ Obtener URL de subida (usando requests directamente para evitar el _request)
            payload = {
                "companyId": company_id or self._get_company_id_from_token(),
                "filename": filename,
                "contentType": content_type
            }
            
            # Hacer la petición directamente (no usar _request porque necesitamos capturar 201)
            url = f"{self.base_url}/medias/generate-upload-url"
            response = self.session.post(url, json=payload)
            
            if response.status_code not in [200, 201]:
                return {
                    "success": False, 
                    "error": f"Error generando URL. Código: {response.status_code}. Respuesta: {response.text[:200]}"
                }
            
            upload_data = response.json()
            upload_url = upload_data["uploadUrl"]
            stored_filename = upload_data["storageFilename"]
            print(f"✅ URL obtenida correctamente")

            # 3️⃣ Subir la imagen a Google Cloud Storage
            print(f"📤 Subiendo archivo a Google Storage...")
            put_headers = {"Content-Type": content_type}
            put_response = requests.put(upload_url, data=file_bytes, headers=put_headers, timeout=60)

            if put_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Error al subir a Google Storage. Código: {put_response.status_code}"
                }
            print(f"✅ Archivo subido correctamente a Storage.")

            # 4️⃣ Obtener dimensiones
            img = Image.open(image_path)
            width, height = img.size

            # 5️⃣ Enviar el mensaje con la imagen al chat
            print(f"📤 Enviando mensaje con imagen al ticket {ticket_id}...")
            message_payload = {
                "messages": [{
                    "id": str(uuid.uuid4()),
                    "body": "",
                    "mimeType": content_type,
                    "fileHash": file_hash,
                    "filename": filename,
                    "storedFilename": stored_filename,
                    "metadata": {"height": height, "width": width},
                    "signMessage": False
                }]
            }
            
            # Este endpoint SÍ devuelve JSON, usamos _request normal
            message_response = self._request("POST", f"/messages/medias/{ticket_id}", data=message_payload)

            return {
                "success": True,
                "message_id": message_response.get("id", ""),
                "data": message_response
            }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Error de red: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error inesperado: {str(e)}"}
    

    def _get_company_id_from_token(self) -> str:
        """
        Intenta extraer el companyId del token JWT
        """
        try:
            # Decodificar parte del token (sin verificar firma)
            import base64
            parts = self.token.split('.')
            if len(parts) == 3:
                payload = parts[1]
                # Ajustar padding
                payload += '=' * (-len(payload) % 4)
                decoded = base64.b64decode(payload)
                data = json.loads(decoded)
                return data.get('companyId', '')
        except:
            pass
        return ""