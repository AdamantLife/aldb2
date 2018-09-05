def do_one(connection):
    connection.execute("""INSERT INTO \"test_table\" (myid, name, value) VALUES (1,"Hello",1);""")

def do_two(connection):
    connection.execute("""INSERT INTO \"test_table\" (name,value) VALUES ("World",2);""")

def do_three(connection):
    connection.execute("""INSERT INTO \"test_table_2\" (linkedid,myvalue) VALUES (1,"Foobar");""")