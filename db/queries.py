from datetime import datetime

from .connection import get_conn, put_conn


def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def get_user_by_net_id(net_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE utd_net_id = %s", (net_id,))
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def create_new_user(first_name, last_name, net_id, email, password, role):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (first_name, last_name, utd_net_id, email, password, role) VALUES (%s, %s, %s, %s, %s, %s) RETURNING user_id",
        (
            first_name,
            last_name,
            net_id,
            email,
            password,
            role,
        ),
    )
    new_user_id = cur.fetchone()["user_id"]
    conn.commit()

    cur.close()
    put_conn(conn)

    return new_user_id


def get_user_by_id(user_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def get_user_signups(user_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT signup_id,
               opp.opp_id,
               title,
               category,
               start_date,
               end_date,
               signup_date,
               status
        FROM signup AS sup,
             opportunities AS opp
        WHERE user_id = %s
          AND sup.opp_id = opp.opp_id
        ORDER BY signup_date DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()

    cur.close()
    put_conn(conn)

    return rows


def get_all_current_opportunities():
    conn = get_conn()
    cur = conn.cursor()

    today = datetime.now()
    date = today.strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT opp_id,
               title,
               opp_image_url,
               category,
               start_date,
               end_date,
               opp.org_id,
               org.org_name
        FROM opportunities AS opp,
             organizations AS org
        WHERE (start_date >= %s OR end_date <= %s)
          AND opp.org_id = org.org_id
        ORDER BY start_date ASC;
        """,
        (
            date,
            date,
        ),
    )
    rows = cur.fetchall()

    cur.close()
    put_conn(conn)

    return rows


def get_all_user_orgs(user_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE org_rep_id = %s", (user_id,))
    rows = cur.fetchall()

    cur.close()
    put_conn(conn)

    return rows


def get_org_by_name(org_name: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE org_name = %s", (org_name,))
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def get_org_details(org_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE org_id = %s", (org_id,))
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def create_new_org(org_name, org_type, org_email, org_image_url, user_id):
    conn = get_conn()
    cur = conn.cursor()

    if len(org_image_url) > 0:
        cur.execute(
            "INSERT INTO organizations (org_name, org_type, org_email, org_image_url, org_rep_id) VALUES (%s, %s, %s, %s, %s)",
            (org_name, org_type, org_email, org_image_url, user_id),
        )
    else:
        cur.execute(
            "INSERT INTO organizations (org_name, org_type, org_email, org_rep_id) VALUES (%s, %s, %s, %s)",
            (org_name, org_type, org_email, user_id),
        )
    conn.commit()

    cur.close()
    put_conn(conn)


def get_opportunity_details(opp_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT opp_id,
               title,
               description,
               opp_image_url,
               category,
               start_date,
               end_date,
               opp.org_id,
               org.org_name
        FROM opportunities AS opp,
             organizations AS org
        WHERE opp_id = %s
          AND opp.org_id = org.org_id
        """,
        (opp_id,),
    )
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row
