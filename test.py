from src.api import WhaticketClient
from src.utils import get_queue_id_by_name, get_tag_id_by_name, get_tickets_by_queue_and_tag

BASE_URL = "https://api.whaticket.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImNmMTc1ZTY4LTljMjQtNGFmMi1hNjFmLTRkNDczMjljM2ZiNCIsInRva2VuVmVyc2lvbiI6MTQzLCJpYXQiOjE3NzM0NzcwNDAsImV4cCI6MTc3MzQ5ODY0MH0.Nh5WxzUhENyCMXRCK8zcoQmNwojgp_3E6lK7_rf3Yjs"

client = WhaticketClient(BASE_URL, TOKEN)

# Opción 1: Manual (paso a paso)
queue_id = get_queue_id_by_name(client, "EN ORIGEN")
tag_id = get_tag_id_by_name(client, "14")
tickets = client.search_tickets(queue_ids=[queue_id], tags_ids=[tag_id])

for ticket in tickets:
    contacto = ticket.get('contact', {}).get('name')
    print(f"{contacto} - {ticket['id']}")