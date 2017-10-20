from app import pg


def pg_sql(sql):
    conn = pg.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
    except Exception as e:
        result = list()
    else:
        cursor.close()
    finally:
        pg.putconn(conn)
    return result
