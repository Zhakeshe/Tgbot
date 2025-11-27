from .database import get_conn

GIFTS_PRESET = [
    (1, "Сердце", "💖", 15, 15 * 9),
    (2, "Мишка", "🧸", 15, 15 * 9),
    (3, "Подарочная коробка", "🎁", 25, 25 * 9),
    (4, "Роза", "🌹", 25, 25 * 9),
    (5, "Торт", "🎂", 50, 50 * 9),
    (6, "Букет", "💐", 50, 50 * 9),
    (7, "Ракета", "🚀", 50, 50 * 9),
    (8, "Кубок", "🏆", 100, 100 * 9),
    (9, "Кольцо", "💍", 100, 100 * 9),
    (10, "Алмаз", "💎", 100, 100 * 9),
    (11, "Шампанское", "🍾", 50, 50 * 9),
]


def seed_gifts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM gifts;")
    count = cur.fetchone()[0]
    if count == 0:
        cur.executemany(
            "INSERT INTO gifts (id, name, emoji, stars, price) VALUES (?, ?, ?, ?, ?)",
            GIFTS_PRESET
        )
        conn.commit()
    conn.close()
# gifts placeholder
