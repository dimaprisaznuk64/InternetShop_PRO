"""Seed color variants with Unsplash product images."""
import argparse
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx


def parse_args():
    parser = argparse.ArgumentParser(description="Seed color variants with product images")
    parser.add_argument("--base-url", default=os.getenv("SEED_BASE_URL", "http://localhost:8000"),
                        help="API base URL (default: $SEED_BASE_URL or http://localhost:8000)")
    parser.add_argument("--admin-email", default=os.getenv("SEED_ADMIN_EMAIL", "admin@example.com"),
                        help="Admin email (default: $SEED_ADMIN_EMAIL)")
    parser.add_argument("--admin-password", default=os.getenv("SEED_ADMIN_PASSWORD", "Admin123!"),
                        help="Admin password (default: $SEED_ADMIN_PASSWORD)")
    return parser.parse_args()


args = parse_args()
base = args.base_url

r = httpx.post(f'{base}/api/auth/login', json={
    'email': args.admin_email, 'password': args.admin_password,
})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r2 = httpx.get(f'{base}/api/products/?limit=50', headers=h)
products = {p['slug']: p for p in r2.json()['products']}

COLOR_VARIANTS = {
    'samsung-galaxy-s24': [
        ('Black', '#1a1a2e', [
            'https://images.unsplash.com/photo-1705585175110-d25f92c183aa?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1678911820864-e2c567c655d7?w=800&h=800&fit=crop',
        ]),
        ('White', '#f5f5f5', [
            'https://images.unsplash.com/photo-1705530292519-ec81f2ace70d?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1565967249821-083c4775e5bc?w=800&h=800&fit=crop',
        ]),
        ('Blue', '#4a90d9', [
            'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800&h=800&fit=crop',
        ]),
    ],
    'iphone-15-pro': [
        ('Natural Titanium', '#8a8a8a', [
            'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&h=800&fit=crop',
        ]),
        ('Blue Titanium', '#4a6fa5', [
            'https://images.unsplash.com/photo-1695048067185-5ab2e3b80957?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1591337676887-a217a6a4e3c8?w=800&h=800&fit=crop',
        ]),
        ('Black Titanium', '#2d2d2d', [
            'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1603891128711-11b4b03bb138?w=800&h=800&fit=crop',
        ]),
    ],
    'xiaomi-14': [
        ('Black', '#1a1a1a', [
            'https://images.unsplash.com/photo-1774437342043-12ffa8880899?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-150677653-a263662b153b?w=800&h=800&fit=crop',
        ]),
        ('White', '#f0f0f0', [
            'https://images.unsplash.com/photo-1774070150575-719b13072230?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1575571536958-38aa1227786a?w=800&h=800&fit=crop',
        ]),
    ],
    'macbook-air-m3': [
        ('Silver', '#c0c0c0', [
            'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=800&h=800&fit=crop',
        ]),
        ('Space Gray', '#5a5a5a', [
            'https://images.unsplash.com/photo-1540630387975-98b9630cc103?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1561909700-7e3abc080cf9?w=800&h=800&fit=crop',
        ]),
    ],
    'asus-rog-strix-g16': [
        ('Black', '#1a1a1a', [
            'https://images.unsplash.com/photo-1771014817844-327a14245bd1?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-06f22a6305090-3e4b4e68e8c9?w=800&h=800&fit=crop',
        ]),
    ],
    'lenovo-thinkpad-x1': [
        ('Black', '#2d2d2d', [
            'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1552257079-e48b715185fa?w=800&h=800&fit=crop',
        ]),
    ],
    'airpods-pro-2': [
        ('White', '#f5f5f5', [
            'https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1505236273191-1dce886b01e9?w=800&h=800&fit=crop',
        ]),
    ],
    'sony-wh-1000xm5': [
        ('Black', '#1a1a1a', [
            'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&h=800&fit=crop',
        ]),
        ('Silver', '#c0c0c0', [
            'https://images.unsplash.com/photo-1619375113153-1631c4fdcfe9?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1621208587196-0b2a7d2aeb03?w=800&h=800&fit=crop',
        ]),
    ],
    'jbl-charge-5': [
        ('Red', '#cc0000', [
            'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1611419010353-e9aed90e8698?w=800&h=800&fit=crop',
        ]),
        ('Blue', '#0066cc', [
            'https://images.unsplash.com/photo-1572764699799-a7ac5e3f8c46?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800&h=800&fit=crop',
        ]),
        ('Black', '#1a1a1a', [
            'https://images.unsplash.com/photo-1767796427185-ada2bf414860?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=800&h=800&fit=crop',
        ]),
    ],
    'galaxy-buds3-pro': [
        ('White', '#f5f5f5', [
            'https://images.unsplash.com/photo-1755182529034-189a6051faae?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=800&h=800&fit=crop',
        ]),
        ('Gray', '#8a8a8a', [
            'https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=800&h=800&fit=crop',
        ]),
    ],
    'magsafe-case-iphone15': [
        ('Clear', '#e0e0e0', [
            'https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1556656793-08538906a9f8?w=800&h=800&fit=crop',
        ]),
        ('Black', '#1a1a1a', [
            'https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=800&h=800&fit=crop',
        ]),
    ],
    'anker-65w-gan': [
        ('White', '#f5f5f5', [
            'https://images.unsplash.com/photo-1625895197185-efcec01cffe0?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&h=800&fit=crop',
        ]),
        ('Black', '#1a1a1a', [
            'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=800&h=800&fit=crop',
            'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&h=800&fit=crop',
        ]),
    ],
}

created = 0
for slug, variants in COLOR_VARIANTS.items():
    if slug not in products:
        print(f'NOT FOUND: {slug}')
        continue

    p = products[slug]
    pid = p['id']

    r3 = httpx.get(f'{base}/api/products/{pid}/images/', headers=h)
    for img in r3.json().get('images', []):
        httpx.delete(f'{base}/api/products/{pid}/images/{img["id"]}', headers=h)

    r4 = httpx.get(f'{base}/api/products/{pid}/variants/', headers=h)
    for v in r4.json().get('variants', []):
        httpx.delete(f'{base}/api/products/{pid}/variants/{v["id"]}', headers=h)

    for color_name, color_hex, img_urls in variants:
        rv = httpx.post(f'{base}/api/products/{pid}/variants/', headers=h, json={
            'name': color_name,
            'sku': f'{p["sku"]}-{color_name.upper().replace(" ", "-")}',
            'price': p['price'],
            'stock': 30,
            'color': color_hex,
        })
        if rv.status_code != 201:
            print(f'  ERROR {slug}/{color_name}: {rv.status_code} {rv.text[:120]}')
            continue
        vid = rv.json()['id']

        for i, url in enumerate(img_urls):
            httpx.post(f'{base}/api/products/{pid}/images/', headers=h, json={
                'url': url,
                'is_primary': i == 0,
                'position': i,
                'variant_id': vid,
            })

        created += 1
        print(f'  {slug:30s} {color_name:20s} ({len(img_urls)} imgs)')

print(f'\nTotal variants created: {created}')

# Verify all images load
print('\nVerifying images...')
ok = 0
fail = 0
r5 = httpx.get(f'{base}/api/products/?limit=50')
for p in r5.json()['products']:
    for img in p['images']:
        try:
            s = httpx.head(img['url'], follow_redirects=True, timeout=5).status_code
            if s == 200:
                ok += 1
            else:
                fail += 1
                print(f'  FAIL [{s}] {p["name"]} -> {img["url"][:70]}')
        except Exception:
            fail += 1
            print(f'  ERR {p["name"]} -> {img["url"][:70]}')
print(f'\nImages: {ok} OK, {fail} FAIL')
