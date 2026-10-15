from typing import Any

from sqlmodel import Session, select

from app.auth.security import hash_password
from app.database import create_db_and_tables, engine
from app.models import Category, Part, User, UserRole
from app.utils import require_id

STAFF_PHONE = "07700000000"
STAFF_PASSWORD = "Staff123!"

OLD_STAFF_PHONE = "0770000000"

categories_data = [
    "CPU",
    "GPU",
    "Motherboard",
    "RAM",
    "Storage",
    "PSU",
    "Case",
    "CPU Cooler",
]

parts_data: list[dict[str, Any]] = [
    {
        "category": "CPU",
        "name": "AMD Ryzen 5 5600",
        "price": 120,
        "stock": 10,
        "socket": "AM4",
        "wattage": 65,
        "specs": "6 cores, 12 threads",
    },
    {
        "category": "CPU",
        "name": "AMD Ryzen 7 5800X",
        "price": 180,
        "stock": 8,
        "socket": "AM4",
        "wattage": 105,
        "specs": "8 cores, 16 threads",
    },
    {
        "category": "CPU",
        "name": "AMD Ryzen 5 7600",
        "price": 200,
        "stock": 10,
        "socket": "AM5",
        "wattage": 65,
        "specs": "6 cores, 12 threads",
    },
    {
        "category": "CPU",
        "name": "Intel Core i5-12400F",
        "price": 150,
        "stock": 12,
        "socket": "LGA1700",
        "wattage": 65,
        "specs": "6 cores, 12 threads",
    },
    {
        "category": "CPU",
        "name": "Intel Core i5-13400F",
        "price": 190,
        "stock": 9,
        "socket": "LGA1700",
        "wattage": 65,
        "specs": "10 cores, 16 threads",
    },
    {
        "category": "CPU",
        "name": "Intel Core i7-13700K",
        "price": 350,
        "stock": 5,
        "socket": "LGA1700",
        "wattage": 125,
        "specs": "16 cores, 24 threads",
    },
    {
        "category": "GPU",
        "name": "NVIDIA RTX 4060",
        "price": 300,
        "stock": 8,
        "wattage": 115,
        "specs": "8GB GDDR6",
    },
    {
        "category": "GPU",
        "name": "NVIDIA RTX 4060 Ti",
        "price": 400,
        "stock": 6,
        "wattage": 160,
        "specs": "8GB GDDR6",
    },
    {
        "category": "GPU",
        "name": "NVIDIA RTX 4070",
        "price": 550,
        "stock": 5,
        "wattage": 200,
        "specs": "12GB GDDR6X",
    },
    {
        "category": "GPU",
        "name": "AMD RX 7600",
        "price": 270,
        "stock": 7,
        "wattage": 165,
        "specs": "8GB GDDR6",
    },
    {
        "category": "GPU",
        "name": "AMD RX 7700 XT",
        "price": 450,
        "stock": 4,
        "wattage": 245,
        "specs": "12GB GDDR6",
    },
    {
        "category": "GPU",
        "name": "AMD RX 7800 XT",
        "price": 500,
        "stock": 4,
        "wattage": 263,
        "specs": "16GB GDDR6",
    },
    {
        "category": "Motherboard",
        "name": "MSI B550M PRO-VDH",
        "price": 100,
        "stock": 8,
        "socket": "AM4",
        "ram_type": "DDR4",
        "form_factor": "mATX",
        "specs": "AMD B550 chipset",
    },
    {
        "category": "Motherboard",
        "name": "ASUS TUF B550-PLUS",
        "price": 140,
        "stock": 6,
        "socket": "AM4",
        "ram_type": "DDR4",
        "form_factor": "ATX",
        "specs": "AMD B550 chipset",
    },
    {
        "category": "Motherboard",
        "name": "MSI PRO B650M-A",
        "price": 150,
        "stock": 7,
        "socket": "AM5",
        "ram_type": "DDR5",
        "form_factor": "mATX",
        "specs": "AMD B650 chipset",
    },
    {
        "category": "Motherboard",
        "name": "ASUS TUF GAMING B650-PLUS",
        "price": 180,
        "stock": 5,
        "socket": "AM5",
        "ram_type": "DDR5",
        "form_factor": "ATX",
        "specs": "AMD B650 chipset",
    },
    {
        "category": "Motherboard",
        "name": "MSI PRO B760M-A",
        "price": 150,
        "stock": 8,
        "socket": "LGA1700",
        "ram_type": "DDR4",
        "form_factor": "mATX",
        "specs": "Intel B760 chipset",
    },
    {
        "category": "Motherboard",
        "name": "ASUS PRIME Z790-P",
        "price": 250,
        "stock": 4,
        "socket": "LGA1700",
        "ram_type": "DDR5",
        "form_factor": "ATX",
        "specs": "Intel Z790 chipset",
    },
    {
        "category": "RAM",
        "name": "Kingston Fury 16GB DDR4",
        "price": 40,
        "stock": 20,
        "ram_type": "DDR4",
        "specs": "16GB, 3200MHz",
    },
    {
        "category": "RAM",
        "name": "Corsair Vengeance 16GB DDR4",
        "price": 45,
        "stock": 18,
        "ram_type": "DDR4",
        "specs": "16GB, 3200MHz",
    },
    {
        "category": "RAM",
        "name": "Kingston Fury 32GB DDR4",
        "price": 75,
        "stock": 12,
        "ram_type": "DDR4",
        "specs": "32GB, 3200MHz",
    },
    {
        "category": "RAM",
        "name": "Corsair Vengeance 16GB DDR5",
        "price": 55,
        "stock": 15,
        "ram_type": "DDR5",
        "specs": "16GB, 5200MHz",
    },
    {
        "category": "RAM",
        "name": "Kingston Fury 32GB DDR5",
        "price": 90,
        "stock": 10,
        "ram_type": "DDR5",
        "specs": "32GB, 5600MHz",
    },
    {
        "category": "RAM",
        "name": "G.Skill Trident Z5 32GB",
        "price": 110,
        "stock": 8,
        "ram_type": "DDR5",
        "specs": "32GB, 6000MHz",
    },
    {
        "category": "Storage",
        "name": "Samsung 980 500GB",
        "price": 50,
        "stock": 15,
        "specs": "NVMe SSD",
    },
    {
        "category": "Storage",
        "name": "Samsung 980 1TB",
        "price": 85,
        "stock": 12,
        "specs": "NVMe SSD",
    },
    {
        "category": "Storage",
        "name": "WD Blue SN570 500GB",
        "price": 45,
        "stock": 15,
        "specs": "NVMe SSD",
    },
    {
        "category": "Storage",
        "name": "WD Black SN770 1TB",
        "price": 90,
        "stock": 10,
        "specs": "NVMe SSD",
    },
    {
        "category": "Storage",
        "name": "Crucial P3 Plus 2TB",
        "price": 120,
        "stock": 7,
        "specs": "NVMe SSD",
    },
    {
        "category": "Storage",
        "name": "Seagate Barracuda 2TB",
        "price": 60,
        "stock": 10,
        "specs": "SATA HDD",
    },
    {
        "category": "PSU",
        "name": "Corsair CV550",
        "price": 55,
        "stock": 10,
        "wattage": 550,
        "specs": "550W 80+ Bronze",
    },
    {
        "category": "PSU",
        "name": "Cooler Master MWE 650",
        "price": 70,
        "stock": 9,
        "wattage": 650,
        "specs": "650W 80+ Bronze",
    },
    {
        "category": "PSU",
        "name": "Corsair RM750e",
        "price": 100,
        "stock": 7,
        "wattage": 750,
        "specs": "750W 80+ Gold",
    },
    {
        "category": "PSU",
        "name": "Corsair RM850e",
        "price": 120,
        "stock": 6,
        "wattage": 850,
        "specs": "850W 80+ Gold",
    },
    {
        "category": "PSU",
        "name": "be quiet! Pure Power 12 1000W",
        "price": 160,
        "stock": 4,
        "wattage": 1000,
        "specs": "1000W 80+ Gold",
    },
    {
        "category": "PSU",
        "name": "MSI MAG A650BN",
        "price": 60,
        "stock": 10,
        "wattage": 650,
        "specs": "650W 80+ Bronze",
    },
    {
        "category": "Case",
        "name": "NZXT H510",
        "price": 80,
        "stock": 8,
        "form_factor": "ATX",
        "specs": "Mid Tower",
    },
    {
        "category": "Case",
        "name": "NZXT H5 Flow",
        "price": 95,
        "stock": 7,
        "form_factor": "ATX",
        "specs": "Mid Tower",
    },
    {
        "category": "Case",
        "name": "Corsair 4000D Airflow",
        "price": 100,
        "stock": 8,
        "form_factor": "ATX",
        "specs": "Mid Tower",
    },
    {
        "category": "Case",
        "name": "Cooler Master TD300 Mesh",
        "price": 80,
        "stock": 6,
        "form_factor": "mATX",
        "specs": "Micro ATX Tower",
    },
    {
        "category": "Case",
        "name": "Lian Li Lancool 216",
        "price": 110,
        "stock": 5,
        "form_factor": "ATX",
        "specs": "Mid Tower",
    },
    {
        "category": "Case",
        "name": "Fractal Design Pop Air",
        "price": 90,
        "stock": 6,
        "form_factor": "ATX",
        "specs": "Mid Tower",
    },
    {
        "category": "CPU Cooler",
        "name": "Cooler Master Hyper 212",
        "price": 40,
        "stock": 12,
        "specs": "Air Cooler",
    },
    {
        "category": "CPU Cooler",
        "name": "DeepCool AK400",
        "price": 35,
        "stock": 15,
        "specs": "Air Cooler",
    },
    {
        "category": "CPU Cooler",
        "name": "DeepCool AK620",
        "price": 65,
        "stock": 8,
        "specs": "Dual Tower Air Cooler",
    },
    {
        "category": "CPU Cooler",
        "name": "Noctua NH-D15",
        "price": 100,
        "stock": 5,
        "specs": "Dual Tower Air Cooler",
    },
    {
        "category": "CPU Cooler",
        "name": "Arctic Liquid Freezer III 240",
        "price": 100,
        "stock": 5,
        "specs": "240mm AIO",
    },
    {
        "category": "CPU Cooler",
        "name": "Corsair H100i 240mm",
        "price": 130,
        "stock": 4,
        "specs": "240mm AIO",
    },
    {
        "category": "GPU",
        "name": "NVIDIA RTX 4080",
        "price": 900,
        "stock": 3,
        "wattage": 320,
        "specs": "16GB GDDR6X",
    },
    {
        "category": "Storage",
        "name": "Samsung 990 Pro 2TB",
        "price": 150,
        "stock": 6,
        "specs": "PCIe 4.0 NVMe SSD",
    },
]


def seed_database() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        category_map: dict[str, Category] = {}

        for category_name in categories_data:
            category = session.exec(select(Category).where(Category.name == category_name)).first()

            if not category:
                category = Category(name=category_name)
                session.add(category)
                session.commit()
                session.refresh(category)

            category_map[category_name] = category

        added_parts = 0

        for part_data in parts_data:
            existing_part = session.exec(select(Part).where(Part.name == part_data["name"])).first()

            if existing_part:
                continue

            category_name = part_data["category"]
            part_fields = {key: value for key, value in part_data.items() if key != "category"}

            part = Part(
                category_id=require_id(category_map[category_name].id),
                **part_fields,
            )

            session.add(part)
            added_parts += 1

        session.commit()

        staff = session.exec(select(User).where(User.phone == STAFF_PHONE)).first()
        old_staff = session.exec(select(User).where(User.phone == OLD_STAFF_PHONE)).first()

        if staff is None and old_staff is not None:
            old_staff.phone = STAFF_PHONE
            old_staff.role = UserRole.STAFF
            session.add(old_staff)
            session.commit()
            print("Demo staff phone fixed (10 digits -> 11 digits).")
        elif staff is not None:
            staff.role = UserRole.STAFF
            session.add(staff)
            session.commit()
            print("Demo staff account already exists.")
        else:
            session.add(
                User(
                    name="Demo Staff",
                    phone=STAFF_PHONE,
                    password_hash=hash_password(STAFF_PASSWORD),
                    role=UserRole.STAFF,
                )
            )
            session.commit()
            print("Demo staff account created successfully.")

        print("Seed completed successfully!")
        print(f"Categories: {len(category_map)}")
        print(f"Parts added: {added_parts}")
        print(f"Demo staff phone: {STAFF_PHONE}")
        print(f"Demo staff password: {STAFF_PASSWORD}")


if __name__ == "__main__":
    seed_database()
