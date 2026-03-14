"""
utils.py - Utilidades para WhaticketAPI
Extractores de IDs, buscadores por nombre y formateadores
"""
from src.api import WhaticketClient 
import requests
import json
from datetime import datetime
import re
from typing import List, Dict, Optional, Any, Union

# ==================== EXTRACTORES DE IDs ====================

def extract_user_ids(users_data: List[Dict]) -> List[Union[int, str]]:
    """
    Extrae solo los IDs de una lista de usuarios
    
    Args:
        users_data: Lista de objetos usuario
    
    Returns:
        [id1, id2, id3, ...]
    """
    ids = []
    for user in users_data:
        if isinstance(user, dict):
            user_id = user.get('id')
            if user_id:
                ids.append(user_id)
    return ids


def extract_queue_ids(queues_data: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extrae nombres e IDs de las colas
    
    Args:
        queues_data: Lista de objetos cola de la API
    
    Returns:
        [{"nombre": "Ventas", "id": "abc123"}, {"nombre": "Soporte", "id": "def456"}, ...]
    """
    queues = []
    
    if not queues_data:
        return queues
    
    for queue in queues_data:
        if isinstance(queue, dict):
            queue_name = queue.get('name', 'SIN NOMBRE')
            queue_id = queue.get('id')
            
            if queue_id:  # Solo si tiene ID válido
                queues.append({
                    "name": queue_name,
                    "id": queue_id
                })
    
    return queues

def get_queue_id_by_name(client: WhaticketClient, queue_name: str) -> str:
    """
    Obtiene el ID de una cola buscándola por su nombre
    
    Args:
        client: Instancia de WhaticketClient (ya autenticado)
        queue_name: Nombre exacto de la cola a buscar
    
    Returns:
        str: ID de la cola o None si no se encuentra
    
    Example:
        queue_id = get_queue_id_by_name(client, "VENTAS")
        if queue_id:
            tickets = client.search_tickets(queue_ids=[queue_id])
    """
    # Obtener todas las colas usando el cliente
    queues_data = client.get_queues()
    
    # Usar tu función extract_queue_ids para obtener la lista formateada
    queues_list = extract_queue_ids(queues_data)
    
    # Buscar por nombre exacto
    for queue in queues_list:
        if queue["name"].upper() == queue_name.upper():  # Case insensitive
            return queue["id"]
    
    # ❌ Este print SOLO se ejecuta si NO encontró nada
    print(f"❌ No se encontró ninguna cola con el nombre '{queue_name}'")
    return None

def extract_tags_info(tags_data: List[Dict]) -> List[Dict]:
    """
    Extrae nombres e IDs de los tags
    
    Args:
        tags_data: Lista de objetos tag de la API
    
    Returns:
        [{"name": "01", "id": "1ade3a12-..."}, {"name": "02", "id": "2976f3d6-..."}, ...]
    """
    tags = []
    
    for tag in tags_data:
        if isinstance(tag, dict):
            tag_name = tag.get('name')
            tag_id = tag.get('id')
            
            if tag_id:
                tags.append({
                    "name": tag_name,
                    "id": tag_id
                })
    
    return tags

def get_tag_id_by_name(client: 'WhaticketClient', tag_name: str) -> str:
    """
    Obtiene el ID de un tag por su nombre
    
    Args:
        client: Instancia de WhaticketClient
        tag_name: Nombre exacto del tag a buscar
    
    Returns:
        str: ID del tag o None si no se encuentra
    """
    tags_data = client.get_tags()
    
    for tag in tags_data:
        if isinstance(tag, dict) and tag.get('name', '').lower() == tag_name.lower():
            return tag.get('id')
    
    print(f"❌ No se encontró ningún tag con el nombre '{tag_name}'")
    return None

def extract_users_info(users_data: List[Dict]) -> List[Dict]:
    """
    [FUNCIÓN 1] Extrae nombres e IDs de todos los usuarios
    
    Args:
        users_data: Lista de objetos usuario de la API
    
    Returns:
        [{"name": "Jordan", "id": "cf175e68-..."}, {"name": "FIORELA", "id": "7cc98466-..."}, ...]
    """
    users = []
    
    for user in users_data:
        if isinstance(user, dict):
            user_name = user.get('name')
            user_id = user.get('id')
            
            if user_id:
                users.append({
                    "name": user_name,
                    "id": user_id
                })
    
    return users

def get_tickets_by_queue_and_tag(client: 'WhaticketClient', queue_name: str, tag_name: str, status: str = "open") -> List[Dict]:
    """
    Obtiene tickets de una cola específica que tengan un tag específico
    
    Args:
        client: Instancia de WhaticketClient
        queue_name: Nombre de la cola
        tag_name: Nombre del tag
        status: Estado del ticket ("open", "pending", etc.)
    
    Returns:
        Lista de tickets que cumplen ambos filtros
    """
    # Obtener IDs
    queue_id = get_queue_id_by_name(client, queue_name)
    tag_id = get_tag_id_by_name(client, tag_name)
    
    if not queue_id:
        print(f"❌ Cola '{queue_name}' no encontrada")
        return []
    
    if not tag_id:
        print(f"❌ Tag '{tag_name}' no encontrado")
        return []
    
    # Buscar tickets
    tickets = client.search_tickets(
        queue_ids=[queue_id],
        tags_ids=[tag_id],
        status=status,
        page=1
    )
    
    return tickets

def get_user_id_by_name(client: 'WhaticketClient', user_name: str) -> str:
    """
    [FUNCIÓN 2] Obtiene el ID de un usuario por su nombre
    
    Args:
        client: Instancia de WhaticketClient
        user_name: Nombre exacto del usuario a buscar
    
    Returns:
        str: ID del usuario o None si no se encuentra
    """
    users_data = client.get_users()
    
    for user in users_data:
        if isinstance(user, dict) and user.get('name', '').lower() == user_name.lower():
            return user.get('id')
    
    print(f"❌ No se encontró ningún usuario con el nombre '{user_name}'")
    return None


def extract_ticket_ids(tickets_data: List[Dict]) -> List[Union[int, str]]:
    """
    Extrae solo los IDs de una lista de tickets
    
    Args:
        tickets_data: Lista de objetos ticket
    
    Returns:
        [id1, id2, id3, ...]
    """
    ids = []
    for ticket in tickets_data:
        if isinstance(ticket, dict):
            ticket_id = ticket.get('id')
            if ticket_id:
                ids.append(ticket_id)
    return ids

def extract_contact_info(ticket_data: Dict) -> Dict:
    """
    Extrae información de contacto de un ticket
    
    Args:
        ticket_data: Objeto ticket
    
    Returns:
        {name: str, phone: str, email: str}
    """
    contact = ticket_data.get('contact', {})
    if not contact and 'ticket' in ticket_data:
        contact = ticket_data['ticket'].get('contact', {})
    
    return {
        'name': contact.get('name', ''),
        'phone': contact.get('number', contact.get('phone', '')),
        'email': contact.get('email', '')
    }

# ==================== BUSCADORES POR NOMBRE ====================

def find_by_name(items: List[Dict], search_term: str, exact: bool = False) -> List[Dict]:
    """
    Busca items cuyo nombre contenga el término
    
    Args:
        items: Lista de objetos con campo 'name'
        search_term: Término a buscar
        exact: True para coincidencia exacta
    
    Returns:
        Items que coinciden con la búsqueda
    """
    if not items:
        return []
    
    search_term = search_term.lower().strip()
    results = []
    
    for item in items:
        if not isinstance(item, dict):
            continue
            
        name = item.get('name', '')
        if not isinstance(name, str):
            name = str(name)
        
        name_lower = name.lower()
        
        if exact:
            if name_lower == search_term:
                results.append(item)
        else:
            if search_term in name_lower:
                results.append(item)
    
    return results

def find_user_by_name(users_data: List[Dict], name: str, exact: bool = False) -> List[Dict]:
    """
    Busca usuarios por nombre
    
    Args:
        users_data: Lista de usuarios
        name: Nombre a buscar
        exact: Coincidencia exacta
    
    Returns:
        Usuarios encontrados
    """
    return find_by_name(users_data, name, exact)


def find_tag_by_name(tags_data: List[Dict], name: str, exact: bool = False) -> List[Dict]:
    """
    Busca tags por nombre
    
    Args:
        tags_data: Lista de tags
        name: Nombre a buscar
        exact: Coincidencia exacta
    
    Returns:
        Tags encontrados
    """
    return find_by_name(tags_data, name, exact)

# ==================== FORMATEADORES DE MENSAJES ====================

def format_message(template: str, parameters: Dict[str, str]) -> str:
    """
    Reemplaza variables en una plantilla
    
    Args:
        template: Plantilla con {variables} o {{variables}}
        parameters: Diccionario con valores
    
    Returns:
        Mensaje formateado
    
    Example:
        template = "Hola {nombre}, tu pedido #{pedido} está listo"
        parameters = {"nombre": "Juan", "pedido": "12345"}
        Resultado: "Hola Juan, tu pedido #12345 está listo"
    """
    result = template
    
    for key, value in parameters.items():
        # Reemplazar ambos formatos: {key} y {{key}}
        result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace(f"{{{key}}}", str(value))
    
    return result

def format_whatsapp_message(text: str) -> str:
    """
    Formatea texto para WhatsApp (escape de caracteres especiales)
    
    Args:
        text: Texto original
    
    Returns:
        Texto formateado para WhatsApp
    """
    # Caracteres que necesitan escape en WhatsApp
    special_chars = ['\\', '*', '_', '~', '`', '>', '[', ']', '(', ')']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def build_ticket_filters(queue_id: Optional[Union[int, str]] = None,
                        status: Optional[str] = None,
                        user_id: Optional[Union[int, str]] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict:
    """
    Construye objeto de filtros eliminando valores None
    
    Args:
        queue_id: ID de cola
        status: Estado
        user_id: ID de usuario
        start_date: Fecha inicio
        end_date: Fecha fin
    
    Returns:
        Diccionario solo con filtros no nulos
    """
    filters = {}
    
    if queue_id is not None:
        filters['queue_id'] = queue_id
    if status is not None:
        filters['status'] = status
    if user_id is not None:
        filters['user_id'] = user_id
    if start_date is not None:
        filters['start_date'] = start_date
    if end_date is not None:
        filters['end_date'] = end_date
    
    return filters

# ==================== VALIDADORES ====================

def validate_ticket_filters(filters: Dict) -> bool:
    """
    Valida que los filtros sean correctos
    
    Args:
        filters: Filtros a validar
    
    Returns:
        True si son válidos
    """
    valid_statuses = ['open', 'pending', 'closed', 'all']
    
    for key, value in filters.items():
        if key == 'status' and value not in valid_statuses:
            return False
        elif key in ['queue_id', 'user_id']:
            try:
                int(value)
            except (ValueError, TypeError):
                return False
        elif key in ['start_date', 'end_date']:
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except (ValueError, TypeError):
                return False
    
    return True

def validate_whatsapp_number(phone_number: str) -> bool:
    """
    Valida formato de número de WhatsApp
    
    Args:
        phone_number: Número a validar
    
    Returns:
        True si es válido
    """
    # Eliminar caracteres no numéricos
    clean_number = re.sub(r'\D', '', phone_number)
    
    # WhatsApp requiere mínimo 10 dígitos (con código de país)
    return len(clean_number) >= 10 and len(clean_number) <= 15

def sanitize_input(text: str) -> str:
    """
    Limpia texto de caracteres peligrosos
    
    Args:
        text: Texto a sanitizar
    
    Returns:
        Texto limpio
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Eliminar caracteres de control y Unicode peligrosos
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Escapar HTML básico
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    return text.strip()

# ==================== UTILIDADES DE FECHAS ====================

def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parsea una fecha en diferentes formatos
    
    Args:
        date_str: String de fecha
    
    Returns:
        Objeto datetime o None
    """
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def format_date_for_api(date: datetime) -> str:
    """
    Formatea fecha para la API
    
    Args:
        date: Objeto datetime
    
    Returns:
        Fecha en formato YYYY-MM-DD
    """
    return date.strftime('%Y-%m-%d')