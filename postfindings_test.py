def unsafe(q):
    # TODO: SQL injection risk
    return db.execute("SELECT * FROM t WHERE x=" + q)
