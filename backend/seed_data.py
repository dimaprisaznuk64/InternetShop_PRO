"""Seed database with sample categories and products."""
import argparse
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx


def parse_args():
    parser = argparse.ArgumentParser(description="Seed database with categories and products")
    parser.add_argument("--base-url", default=os.getenv("SEED_BASE_URL", "http://localhost:8000"),
                        help="API base URL (default: $SEED_BASE_URL or http://localhost:8000)")
    parser.add_argument("--admin-email", default=os.getenv("SEED_ADMIN_EMAIL", "admin@example.com"),
                        help="Admin email (default: $SEED_ADMIN_EMAIL or admin@example.com)")
    parser.add_argument("--admin-password", default=os.getenv("SEED_ADMIN_PASSWORD", "Admin123!"),
                        help="Admin password (default: $SEED_ADMIN_PASSWORD)")
    return parser.parse_args()


async def main():
    args = parse_args()
    async with httpx.AsyncClient(base_url=args.base_url) as client:
        # Login as admin
        r = await client.post("/api/auth/login", json={
            "email": args.admin_email, "password": args.admin_password,
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create categories
        cats = [
            {"name": "Смартфони", "slug": "smartphones"},
            {"name": "Ноутбуки", "slug": "laptops"},
            {"name": "Аудіо", "slug": "audio"},
            {"name": "Аксесуари", "slug": "accessories"},
        ]
        cat_ids = []
        for c in cats:
            r = await client.post("/api/categories/", json=c, headers=headers)
            data = r.json()
            cat_ids.append(data["id"])
            print(f"Category: {c['name']} -> {data['id']}")

        # Create products
        products = [
            {
                "name": "Samsung Galaxy S24",
                "slug": "samsung-galaxy-s24",
                "description": "Флагманський смартфон Samsung з AI можливостями",
                "price": "32999.00",
                "sku": "SAM-S24-001",
                "stock": 25,
                "category_id": cat_ids[0],
                "brand": "Samsung",
            },
            {
                "name": "iPhone 15 Pro",
                "slug": "iphone-15-pro",
                "description": "Найпотужніший iPhone з титановим корпусом",
                "price": "45999.00",
                "sku": "APL-15P-001",
                "stock": 15,
                "category_id": cat_ids[0],
                "brand": "Apple",
            },
            {
                "name": "Xiaomi 14",
                "slug": "xiaomi-14",
                "description": "Смартфон Xiaomi з камерою Leica",
                "price": "24999.00",
                "sku": "XMI-14-001",
                "stock": 30,
                "category_id": cat_ids[0],
                "brand": "Xiaomi",
            },
            {
                "name": "MacBook Air M3",
                "slug": "macbook-air-m3",
                "description": "Ультратонкий ноутбук Apple з чипом M3",
                "price": "52999.00",
                "sku": "APL-MBA-M3",
                "stock": 10,
                "category_id": cat_ids[1],
                "brand": "Apple",
            },
            {
                "name": "ASUS ROG Strix G16",
                "slug": "asus-rog-strix-g16",
                "description": "Ігровий ноутбук з RTX 4070",
                "price": "44999.00",
                "sku": "ASUS-G16-001",
                "stock": 8,
                "category_id": cat_ids[1],
                "brand": "ASUS",
            },
            {
                "name": "Lenovo ThinkPad X1 Carbon",
                "slug": "lenovo-thinkpad-x1",
                "description": "Бізнес-ноутбук з OLED дисплеєм",
                "price": "39999.00",
                "sku": "LEN-X1C-001",
                "stock": 12,
                "category_id": cat_ids[1],
                "brand": "Lenovo",
            },
            {
                "name": "AirPods Pro 2",
                "slug": "airpods-pro-2",
                "description": "Бездротові навушники Apple з шумозаглушенням",
                "price": "8999.00",
                "sku": "APL-APP2-001",
                "stock": 50,
                "category_id": cat_ids[2],
                "brand": "Apple",
            },
            {
                "name": "Sony WH-1000XM5",
                "slug": "sony-wh-1000xm5",
                "description": "Навушники Sony з найкращим шумозаглушенням",
                "price": "12999.00",
                "sku": "SNY-WH5-001",
                "stock": 20,
                "category_id": cat_ids[2],
                "brand": "Sony",
            },
            {
                "name": "JBL Charge 5",
                "slug": "jbl-charge-5",
                "description": "Портативна колонка JBL з водозахистом",
                "price": "4999.00",
                "sku": "JBL-CH5-001",
                "stock": 35,
                "category_id": cat_ids[2],
                "brand": "JBL",
            },
            {
                "name": "Samsung Galaxy Buds3 Pro",
                "slug": "galaxy-buds3-pro",
                "description": "Бездротові навушники Samsung з AI",
                "price": "6499.00",
                "sku": "SAM-GB3P-001",
                "stock": 40,
                "category_id": cat_ids[2],
                "brand": "Samsung",
            },
            {
                "name": "Чохол MagSafe для iPhone 15",
                "slug": "magsafe-case-iphone15",
                "description": "Оригінальний чохол Apple з MagSafe",
                "price": "1999.00",
                "sku": "APL-CASE-15",
                "stock": 100,
                "category_id": cat_ids[3],
                "brand": "Apple",
            },
            {
                "name": "Зарядка Anker 65W GaN",
                "slug": "anker-65w-gan",
                "description": "Компактна зарядка USB-C 65W",
                "price": "2499.00",
                "sku": "ANK-65W-001",
                "stock": 60,
                "category_id": cat_ids[3],
                "brand": "Anker",
            },
        ]

        for p in products:
            r = await client.post("/api/products/", json=p, headers=headers)
            if r.status_code == 201:
                pid = r.json()["id"]
                print(f"Product: {p['name']} -> {pid}")
            else:
                print(f"ERROR {p['name']}: {r.status_code} {r.text}")

        # Add product images (using placeholder URLs from picsum)
        r = await client.get("/api/products/", headers=headers)
        all_products = r.json()["products"]
        for i, prod in enumerate(all_products):
            # Add 2 images per product
            for j in range(2):
                img_url = f"https://picsum.photos/seed/{prod['slug']}/{j+1}/800/800"
                await client.post(
                    f"/api/products/{prod['id']}/images",
                    json={"url": img_url, "is_primary": j == 0, "position": j},
                    headers=headers,
                )
            # Add variants for smartphones
            if prod.get("category_id") == cat_ids[0]:
                for variant in [
                    {"name": "128GB Black", "sku": f"{prod['sku']}-128B", "price": prod["price"], "stock": 10, "attributes": '{"color":"Black","storage":"128GB"}'},
                    {"name": "256GB White", "sku": f"{prod['sku']}-256W", "price": str(float(prod["price"]) + 5000), "stock": 8, "attributes": '{"color":"White","storage":"256GB"}'},
                ]:
                    await client.post(
                        f"/api/products/{prod['id']}/variants",
                        json=variant,
                        headers=headers,
                    )
            print(f"Images + variants added for: {prod['name']}")

        print(f"\nDone! Refresh {args.base_url.replace(':8000', ':3000')}")


if __name__ == "__main__":
    asyncio.run(main())
