"""SQLite database with Lisbon metro area seed data."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "demo.db"


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection, seeding on first access."""
    needs_seed = not DB_PATH.exists()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if needs_seed:
        _seed(conn)
    return conn


def _seed(conn: sqlite3.Connection) -> None:
    """Create schema and insert demo data for the Lisbon metro area."""
    conn.executescript(
        """
        CREATE TABLE neighborhoods (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            population INTEGER,
            avg_income REAL,
            safety_score REAL,
            transport_score REAL,
            walkability_score REAL
        );

        CREATE TABLE properties (
            id INTEGER PRIMARY KEY,
            neighborhood_id INTEGER REFERENCES neighborhoods(id),
            title TEXT NOT NULL,
            type TEXT NOT NULL,        -- apartment, house, studio, penthouse
            price REAL NOT NULL,
            area_m2 REAL NOT NULL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            floor INTEGER,
            has_parking INTEGER DEFAULT 0,
            has_terrace INTEGER DEFAULT 0,
            energy_rating TEXT,
            listed_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',  -- active, sold, withdrawn
            description TEXT
        );

        CREATE TABLE price_history (
            id INTEGER PRIMARY KEY,
            property_id INTEGER REFERENCES properties(id),
            price REAL NOT NULL,
            changed_date TEXT NOT NULL,
            event TEXT DEFAULT 'price_change'  -- listed, price_change, sold
        );

        CREATE TABLE amenities (
            id INTEGER PRIMARY KEY,
            neighborhood_id INTEGER REFERENCES neighborhoods(id),
            name TEXT NOT NULL,
            type TEXT NOT NULL,  -- school, hospital, metro, supermarket, park, gym
            distance_km REAL
        );

        CREATE TABLE market_snapshots (
            id INTEGER PRIMARY KEY,
            neighborhood_id INTEGER REFERENCES neighborhoods(id),
            month TEXT NOT NULL,        -- YYYY-MM
            avg_price_m2 REAL,
            listings_count INTEGER,
            avg_days_on_market INTEGER,
            sold_count INTEGER
        );

        -- Neighborhoods
        INSERT INTO neighborhoods VALUES
            (1, 'Chiado', 'Lisbon', 3800, 42000, 7.5, 9.2, 9.5),
            (2, 'Alfama', 'Lisbon', 4200, 28000, 6.8, 8.5, 8.0),
            (3, 'Príncipe Real', 'Lisbon', 3100, 48000, 8.2, 8.8, 9.0),
            (4, 'Parque das Nações', 'Lisbon', 22000, 38000, 8.8, 9.5, 8.5),
            (5, 'Cascais Centro', 'Cascais', 35000, 45000, 9.0, 7.0, 8.8),
            (6, 'Almada', 'Almada', 55000, 22000, 7.0, 7.5, 7.2);

        -- Properties
        INSERT INTO properties (id, neighborhood_id, title, type, price, area_m2, bedrooms, bathrooms, floor, has_parking, has_terrace, energy_rating, listed_date, status, description) VALUES
            (1, 1, 'Renovated Chiado Apartment', 'apartment', 520000, 85, 2, 1, 3, 0, 0, 'B', '2026-02-15', 'active', 'Bright 2-bed in the heart of Chiado, recently renovated with original hardwood floors'),
            (2, 1, 'Chiado Penthouse with Terrace', 'penthouse', 980000, 140, 3, 2, 6, 1, 1, 'A', '2026-01-10', 'active', 'Stunning penthouse with panoramic river views and private rooftop terrace'),
            (3, 2, 'Alfama Traditional Flat', 'apartment', 310000, 65, 1, 1, 2, 0, 0, 'D', '2026-03-01', 'active', 'Charming 1-bed in historic Alfama, steps from the cathedral'),
            (4, 2, 'Alfama Renovated Studio', 'studio', 195000, 38, 0, 1, 1, 0, 0, 'C', '2026-01-20', 'sold', 'Modern studio ideal for short-term rental, sold above asking'),
            (5, 3, 'Príncipe Real Garden Flat', 'apartment', 680000, 110, 3, 2, 2, 1, 1, 'B', '2025-12-05', 'active', 'Elegant apartment facing the botanical garden'),
            (6, 4, 'Expo T3 with River View', 'apartment', 450000, 95, 3, 2, 8, 1, 1, 'A', '2026-03-10', 'active', 'Modern 3-bed in Expo area with Vasco da Gama bridge views'),
            (7, 4, 'Parque das Nações Studio', 'studio', 210000, 42, 0, 1, 4, 1, 0, 'A', '2026-02-28', 'active', 'Efficient studio near Oceanarium, perfect for young professionals'),
            (8, 5, 'Cascais Seafront Villa', 'house', 1250000, 220, 4, 3, 0, 1, 1, 'B', '2026-01-15', 'active', 'Detached villa 200m from the beach, private garden'),
            (9, 5, 'Cascais Centre Apartment', 'apartment', 395000, 78, 2, 1, 1, 0, 0, 'C', '2026-04-01', 'active', 'Walking distance to Cascais marina and train station'),
            (10, 6, 'Almada T2 with Parking', 'apartment', 185000, 72, 2, 1, 5, 1, 0, 'B', '2026-03-15', 'active', 'Affordable 2-bed with river crossing in under 15 min');

        -- Price history
        INSERT INTO price_history (property_id, price, changed_date, event) VALUES
            (1, 545000, '2026-02-15', 'listed'),
            (1, 520000, '2026-03-20', 'price_change'),
            (2, 980000, '2026-01-10', 'listed'),
            (3, 310000, '2026-03-01', 'listed'),
            (4, 185000, '2026-01-20', 'listed'),
            (4, 195000, '2026-02-10', 'sold'),
            (5, 720000, '2025-12-05', 'listed'),
            (5, 680000, '2026-02-15', 'price_change'),
            (6, 450000, '2026-03-10', 'listed'),
            (8, 1300000, '2026-01-15', 'listed'),
            (8, 1250000, '2026-03-01', 'price_change'),
            (10, 185000, '2026-03-15', 'listed');

        -- Amenities
        INSERT INTO amenities (neighborhood_id, name, type, distance_km) VALUES
            (1, 'Baixa-Chiado Metro', 'metro', 0.1),
            (1, 'Escola Secundária Passos Manuel', 'school', 0.4),
            (1, 'Pingo Doce Chiado', 'supermarket', 0.2),
            (2, 'Santa Apolónia Metro', 'metro', 0.5),
            (2, 'Hospital de São José', 'hospital', 0.8),
            (3, 'Rato Metro', 'metro', 0.3),
            (3, 'Jardim Botânico', 'park', 0.1),
            (3, 'Continente Bom Dia', 'supermarket', 0.3),
            (4, 'Oriente Metro', 'metro', 0.2),
            (4, 'Hospital CUF Descobertas', 'hospital', 0.5),
            (4, 'Parque das Nações Park', 'park', 0.1),
            (4, 'Holmes Place Expo', 'gym', 0.4),
            (5, 'Cascais Train Station', 'metro', 0.3),
            (5, 'Hospital de Cascais', 'hospital', 1.2),
            (5, 'Praia de Cascais', 'park', 0.2),
            (6, 'Almada Metro (MST)', 'metro', 0.6),
            (6, 'Hospital Garcia de Orta', 'hospital', 1.5);

        -- Market snapshots (6 months)
        INSERT INTO market_snapshots (neighborhood_id, month, avg_price_m2, listings_count, avg_days_on_market, sold_count) VALUES
            (1, '2025-11', 5800, 45, 62, 12),
            (1, '2025-12', 5850, 42, 58, 14),
            (1, '2026-01', 5920, 48, 55, 16),
            (1, '2026-02', 6010, 51, 52, 18),
            (1, '2026-03', 6100, 47, 48, 20),
            (1, '2026-04', 6180, 50, 45, 19),
            (4, '2025-11', 4200, 78, 45, 28),
            (4, '2025-12', 4250, 72, 42, 30),
            (4, '2026-01', 4300, 80, 40, 32),
            (4, '2026-02', 4380, 85, 38, 35),
            (4, '2026-03', 4450, 82, 36, 33),
            (4, '2026-04', 4520, 79, 35, 31),
            (6, '2025-11', 2100, 120, 75, 35),
            (6, '2025-12', 2120, 115, 72, 38),
            (6, '2026-01', 2150, 125, 70, 40),
            (6, '2026-02', 2180, 130, 68, 42),
            (6, '2026-03', 2200, 128, 65, 44),
            (6, '2026-04', 2240, 122, 62, 41);
        """
    )
    conn.commit()
