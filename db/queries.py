from datetime import datetime

from .connection import get_conn, put_conn


# ********************************
# queries for users table
# ********************************
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


def get_user_by_id(user_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
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


# ********************************
# queries for organizations table
# ********************************
def get_all_user_orgs(user_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE org_rep_id = %s", (user_id,))
    rows = cur.fetchall()

    cur.close()
    put_conn(conn)

    return rows


def get_all_non_user_orgs(user_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE org_rep_id <> %s", (user_id,))
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

    cur.execute(
        """
        SELECT org_id,
               org_name,
               org_type,
               org_image_url,
               org_email,
               u.first_name,
               u.last_name,
               u.email AS org_rep_email
        FROM organizations AS org,
             users AS u
        WHERE org_id = %s
          AND org.org_rep_id = u.user_id""",
        (org_id,),
    )
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


def update_org(org_name, org_type, org_email, org_image_url, org_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE organizations
        SET org_name      = %s,
            org_type      = %s,
            org_email     = %s,
            org_image_url = %s
        WHERE org_id = %s
        """,
        (org_name, org_type, org_email, org_image_url, org_id),
    )
    conn.commit()

    cur.close()
    put_conn(conn)


def delete_org(org_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE
        FROM organizations
        WHERE org_id = %s
        """,
        (org_id,),
    )
    conn.commit()

    cur.close()
    put_conn(conn)


def check_is_representative(user_id: int, org_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM organizations WHERE org_id = %s AND org_rep_id = %s",
        (org_id, user_id),
    )
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


# ********************************
# queries for opportunities table
# ********************************
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


def get_all_current_opportunities_for_org(org_id: int):
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
               max_signups,
               opp.org_id,
               org.org_name
        FROM opportunities AS opp,
             organizations AS org
        WHERE (start_date >= %s OR end_date >= %s)
          AND opp.org_id = org.org_id
          AND opp.org_id = %s
        ORDER BY start_date ASC;
        """,
        (
            date,
            date,
            org_id,
        ),
    )
    rows = cur.fetchall()

    cur.close()
    put_conn(conn)

    return rows


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
               max_signups,
               opp.org_id,
               org.org_name,
               org.org_rep_id
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


def get_opportunity_for_org_by_title(org_id: int, title: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM opportunities WHERE org_id = %s AND title = %s",
        (org_id, title),
    )
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def get_max_signups(opp_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT max_signups FROM opportunities WHERE opp_id = %s",
        (opp_id,),
    )
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    max_signups = row["max_signups"]

    if max_signups:
        max_signups = int(max_signups)

    return max_signups


def create_new_opportunity(
        title,
        opp_image_url,
        description,
        category,
        start_date,
        end_date,
        max_signups,
        org_id,
):
    conn = get_conn()
    cur = conn.cursor()

    if len(opp_image_url) > 0:
        cur.execute(
            "INSERT INTO opportunities (title, opp_image_url, description, category, start_date, end_date, max_signups, org_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                title,
                opp_image_url,
                description,
                category,
                start_date,
                end_date,
                max_signups,
                org_id,
            ),
        )
    else:
        cur.execute(
            "INSERT INTO opportunities (title, description, category, start_date, end_date, max_signups, org_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                title,
                description,
                category,
                start_date,
                end_date,
                max_signups,
                org_id,
            ),
        )
    conn.commit()

    cur.close()
    put_conn(conn)


def update_opp(
        title,
        opp_image_url,
        description,
        category,
        start_date,
        end_date,
        max_signups,
        opp_id,
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE opportunities
        SET title         = %s,
            description   = %s,
            category      = %s,
            opp_image_url = %s,
            start_date    = %s,
            end_date      = %s,
            max_signups   = %s
        WHERE opp_id = %s
        """,
        (
            title,
            description,
            category,
            opp_image_url,
            start_date,
            end_date,
            max_signups,
            opp_id,
        ),
    )
    conn.commit()

    cur.close()
    put_conn(conn)


def delete_opp(opp_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE
        FROM opportunities
        WHERE opp_id = %s
        """,
        (opp_id,),
    )
    conn.commit()

    cur.close()
    put_conn(conn)


# ********************************
# queries for signup table
# ********************************
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


def get_all_signups_for_org(org_id):
    conn = get_conn()
    cur = conn.cursor()

    today = datetime.now()
    date = today.strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT sup.signup_id,
               opp.opp_id,
               opp.title,
               opp.start_date,
               opp.end_date,
               u.user_id,
               u.first_name,
               u.last_name,
               u.email,
               sup.signup_date,
               sup.status
        FROM opportunities AS opp
                 LEFT JOIN signup AS sup ON sup.opp_id = opp.opp_id
                 LEFT JOIN users AS u ON sup.user_id = u.user_id
        WHERE opp.org_id = %s
          AND (opp.start_date >= %s OR opp.end_date <= %s)
        ORDER BY opp.start_date ASC, sup.signup_date ASC;
        """,
        (
            org_id,
            date,
            date,
        ),
    )
    rows = cur.fetchall()

    cur.close()
    put_conn(conn)

    return rows


def get_signup_details_by_id(signup_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT sup.signup_id, sup.user_id, sup.opp_id, org.org_rep_id
        FROM signup AS sup,
             organizations AS org,
             opportunities AS opp
        WHERE sup.signup_id = %s
          AND sup.opp_id = opp.opp_id
          AND opp.org_id = org.org_id
        """,
        (signup_id,),
    )
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def get_signup_by_user_and_opp(user_id: int, opp_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM signup WHERE user_id = %s AND opp_id = %s",
        (
            user_id,
            opp_id,
        ),
    )
    row = cur.fetchone()

    cur.close()
    put_conn(conn)

    return row


def get_signup_count_for_opp(opp_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM signup WHERE opp_id = %s",
        (opp_id,),
    )
    row = cur.fetchone()

    signup_count = row["count"]
    if signup_count:
        signup_count = int(signup_count)
    else:
        signup_count = 0

    cur.close()
    put_conn(conn)

    return signup_count


def create_new_signup(user_id: int, opp_id: int):
    conn = get_conn()
    cur = conn.cursor()

    today = datetime.now()
    date = today.strftime("%Y-%m-%d")

    cur.execute(
        "INSERT INTO signup (user_id, opp_id, signup_date) VALUES (%s, %s, %s)",
        (
            user_id,
            opp_id,
            date,
        ),
    )
    conn.commit()

    cur.close()
    put_conn(conn)


def delete_user_signup(signup_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE
        FROM signup
        WHERE signup_id = %s
        """,
        (signup_id,),
    )
    conn.commit()

    cur.close()
    put_conn(conn)
