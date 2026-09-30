from app.database.connection import get_connection, get_placeholder, supports_returning, fetch_new_id


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
    ph = get_placeholder()
    cursor.execute(
        f"SELECT * FROM users WHERE phone = {ph}",
        (normalized,),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return dict(existing)

    insert_sql = f"INSERT INTO users (name, phone) VALUES ({ph}, {ph})"
    if supports_returning():
        insert_sql += " RETURNING id"
    cursor.execute(insert_sql, (name, normalized))
    conn.commit()
    user_id = fetch_new_id(cursor)
    conn.close()
    return {"id": user_id, "name": name, "phone": normalized}


def get_user_by_phone(phone):
    """Busca um usuário pelo número de telefone."""
    normalized = normalize_phone(phone)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE phone = {get_placeholder()}", (normalized,))
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
    ph = get_placeholder()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM alerts WHERE user_id = {ph} AND product_id = {ph} AND active IS TRUE",
        (user_id, product_id),
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError("alerta já existe para esse usuário e produto")

    insert_sql = f"INSERT INTO alerts (user_id, product_id, threshold_percent, active) VALUES ({ph}, {ph}, {ph}, TRUE)"
    if supports_returning():
        insert_sql += " RETURNING id"
    cursor.execute(insert_sql, (user_id, product_id, threshold))
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
        f"SELECT * FROM alerts WHERE user_id = {get_placeholder()} ORDER BY id DESC",
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
        f"SELECT a.*, u.phone, u.name FROM alerts a JOIN users u ON u.id = a.user_id WHERE a.product_id = {get_placeholder()} AND a.active IS TRUE",
        (product_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
