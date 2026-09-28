from app.database.connection import get_connection


def normalize_phone(phone):
    """Normaliza o telefone para evitar duplicidade e entradas inconsistentes."""
    if not phone:
        return None
    return "".join(ch for ch in str(phone) if ch.isdigit() or ch in "+")


def create_user(name=None, phone=None):
    """Cria um usuário para receber alertas de preços."""
    normalized = normalize_phone(phone)
    if not normalized:
        raise ValueError("phone é obrigatório")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE phone = ?",
        (normalized,),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return dict(existing)

    cursor.execute(
        "INSERT INTO users (name, phone) VALUES (?, ?)",
        (name, normalized),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"id": user_id, "name": name, "phone": normalized}


def get_user_by_phone(phone):
    """Busca um usuário pelo número de telefone."""
    normalized = normalize_phone(phone)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (normalized,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_users():
    """Lista todos os usuários cadastrados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_alert(user_id, product_id, threshold_percent=10.0):
    """Salva um alerta configurado para um produto e usuário."""
    if user_id is None or product_id is None:
        raise ValueError("user_id e product_id são obrigatórios")

    threshold = float(threshold_percent)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM alerts WHERE user_id = ? AND product_id = ? AND active = 1",
        (user_id, product_id),
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError("alerta já existe para esse usuário e produto")

    cursor.execute(
        "INSERT INTO alerts (user_id, product_id, threshold_percent, active) VALUES (?, ?, ?, 1)",
        (user_id, product_id, threshold),
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return {
        "id": alert_id,
        "user_id": user_id,
        "product_id": product_id,
        "threshold_percent": threshold,
        "active": True,
    }


def list_alerts(user_id):
    """Lista alertas de um usuário."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM alerts WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_alerts_for_product(product_id):
    """Lista usuários e alertas vinculados a um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT a.*, u.phone, u.name FROM alerts a JOIN users u ON u.id = a.user_id WHERE a.product_id = ? AND a.active = 1",
        (product_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
