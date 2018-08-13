import os
import subprocess

def show_todo(conn):
    cursor = conn.cursor()
    query = ("SELECT id, content FROM t_todo WHERE status = 0")
    cursor.execute(query)
    print("work to do:")
    for (id, content) in cursor:
        print(" " * 4 + "{}: {}".format(id, content))
    cursor.close()

def show_done(conn):
    cursor = conn.cursor()
    query = ("SELECT id, content FROM t_todo WHERE status = 1")
    cursor.execute(query)
    print("work have done:")
    for (id, content) in cursor:
        print(" " * 4 + "{}: {}".format(id, content))
    cursor.close()

def add_todo(conn, add):
    cursor = conn.cursor()
    insert = ("INSERT INTO t_todo (content) VALUES ('{}')".format(add))
    cursor.execute(insert)
    print("add todo success")
    conn.commit()
    cursor.close()

def kill_todo(conn, kill):
    EDITOR = os.environ.get('EDITOR','vim')
    file_name = './answer';
    subprocess.call([EDITOR, file_name])
    with open(file_name, 'r') as f:
        f.readline()
        answer = f.read()
    cursor = conn.cursor()
    update = ("UPDATE t_todo SET status = 1, answer = '{}' WHERE id = {}".format(answer, kill))
    cursor.execute(update)
    conn.commit()
    print("kill todo success")
    subprocess.getoutput("sed -ie '2,$d' answer")
    cursor.close()


def commit_diff_stat(conn, dirs):
    cursor = conn.cursor()
    for dir in dirs:
        print(dir)
        os.chdir(dir)
        svnst = 'svn st'
        svnstout = subprocess.getoutput(svnst)
        if len(svnstout) == 0:
            print("no code change to commit")
            continue
        cmd = 'svn diff --diff-cmd diff | diffstat'
        out = subprocess.getoutput(cmd)
        try:
            insertion = out.split('\n')[-1:][0].split(',')[1].split(' ')[1]
            deletion = out.split('\n')[-1:][0].split(',')[2].split(' ')[1]
        except Exception:
            return
        detail = out
        insert = ("INSERT INTO t_line (insertion, deletion, detail) VALUES (%s, %s, %s)")
        cursor.execute(insert, (insertion, deletion, detail))
        print("count code success, path: {}".format(dir))
        print("detail: \n")
        print(out)
    conn.commit()
    cursor.close

def count_line_today(conn):
    cursor = conn.cursor()
    query = ("select sum(insertion) as insertions, sum(deletion) as deletions "
             "from t_line where created > date_sub(now(), interval 1 day)")
    cursor.execute(query)
    for (insertions, deletions) in cursor:
        print("today's work")
        print(' ' * 4 + "insertions: {}, deletions: {}".format(insertions, deletions))

