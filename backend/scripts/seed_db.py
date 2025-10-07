"""
Seed script to create initial Fleet Manager accounts and sample data.
Run this after database migration: python scripts/seed_db.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.models import User, Vehicle, UserRole, VehicleStatus

async def seed_database():
    async with AsyncSessionLocal() as session:
        print("🌱 Seeding database...")
        
        # Create Fleet Manager accounts
        fleet_managers = [
            User(
                name="John Manager",
                email="manager1@fleetwise.com",
                employee_id="FM001",
                phone="555-0101",
                password_hash=get_password_hash("Manager@123"),
                role=UserRole.FLEET_MANAGER,
                reservation_count=0,
                email_verified=True
            ),
            User(
                name="Sarah Admin",
                email="manager2@fleetwise.com",
                employee_id="FM002",
                phone="555-0102",
                password_hash=get_password_hash("Manager@456"),
                role=UserRole.FLEET_MANAGER,
                reservation_count=0,
                email_verified=True
            )
        ]
        
        for manager in fleet_managers:
            session.add(manager)
        
        print("✅ Created 2 Fleet Manager accounts")
        print("   - manager1@fleetwise.com / Manager@123")
        print("   - manager2@fleetwise.com / Manager@456")
        
        # Create sample vehicles
        vehicles = [
            # Honda vehicles
            Vehicle(manufacturer="Honda", model="Civic", license_plate="ABC-1234", status=VehicleStatus.AVAILABLE),
            Vehicle(manufacturer="Honda", model="Accord", license_plate="ABC-1235", status=VehicleStatus.AVAILABLE),
            Vehicle(manufacturer="Honda", model="CR-V", license_plate="ABC-1236", status=VehicleStatus.AVAILABLE),
            
            # Toyota vehicles
            Vehicle(manufacturer="Toyota", model="Camry", license_plate="XYZ-7890", status=VehicleStatus.AVAILABLE),
            Vehicle(manufacturer="Toyota", model="Corolla", license_plate="XYZ-7891", status=VehicleStatus.AVAILABLE),
            Vehicle(manufacturer="Toyota", model="RAV4", license_plate="XYZ-7892", status=VehicleStatus.AVAILABLE),
            
            # Ford vehicles
            Vehicle(manufacturer="Ford", model="Focus", license_plate="DEF-4567", status=VehicleStatus.AVAILABLE),
            Vehicle(manufacturer="Ford", model="Escape", license_plate="DEF-4568", status=VehicleStatus.AVAILABLE),
            Vehicle(manufacturer="Ford", model="F-150", license_plate="DEF-4569", status=VehicleStatus.AVAILABLE),
        ]
        
        for vehicle in vehicles:
            session.add(vehicle)
        
        print("✅ Created 9 sample vehicles (3 Honda, 3 Toyota, 3 Ford)")
        
        await session.commit()
        print("🎉 Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())