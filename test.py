from src.api import WhaticketClient

BASE_URL = "https://api.whaticket.com"
token = input("🔑 Token: ").strip()

client = WhaticketClient(BASE_URL, token)

if not client.validate_token():
    print("❌ Token inválido")
    exit()

print("\n📋 COLAS:")
colas = client.get_queues()
for c in colas[:5]:
    print(f"  - {c['name']} ({c['id']})")

print("\n📋 TICKETS ABIERTOS:")
tickets = client.search_tickets(status="open")
print(f"  Total: {len(tickets)}")
for t in tickets[:3]:
    nombre = t.get('contact', {}).get('name', 'Sin nombre')
    print(f"  - {nombre}: {t.get('lastMessage', '...')[:30]}")

print("\n✅ Listo")