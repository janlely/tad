import os
import subprocess
import time
import datetime
from collections import OrderedDict

def getMonStartTime():
    l = time.localtime(time.time())
    days_to_mon = l.tm_wday
    t = (l.tm_year, l.tm_mon, l.tm_mday, 0, 0, 0, l.tm_wday, l.tm_yday, 0)
    tt = time.mktime(t)
    return tt - days_to_mon * 86400

def show_todo(conn, show_all):
    cursor = conn.cursor()
    query = '''
        SELECT t2.id, t2.content, t1.name
        FROM t_topic t1
        LEFT JOIN t_todo t2
        ON t1.id = t2.topic_id
        WHERE t1.current = 1
        AND t2.status = 0
    '''
    if show_all:
        query = '''
            SELECT t2.id, t2.content, t1.name
            FROM t_topic t1
            LEFT JOIN t_todo t2
            ON t1.id = t2.topic_id
            WHERE t2.status = 0
        '''
    cursor.execute(query)
    print("work to do:")
    for (id, content, name) in cursor:
        content = content.replace('\n', '\n        ')
        print(" " * 4 + "{}: {}\n        {}".format(id, name, content))
    cursor.close()

def show_trifles(conn):
    cursor = conn.cursor()
    query = '''
    SELECT id, content, created
    FROM t_trifles
    ORDER BY created
    '''
    cursor.execute(query)
    trifles_dict = OrderedDict()
    for id, content, created in cursor:
        date = datetime.datetime.fromtimestamp(int(created.timestamp()))
        date_str = date.strftime("%Y-%m-%d")
        if not date_str in trifles_dict:
            trifles_dict[date_str] = []
        trifles_dict[date_str].append(content)
    for key in trifles_dict.keys():
        print("    {}:".format(key))
        for content in trifles_dict[key]:
            print("    {}".format(content))

def show_done(conn):
    cursor = conn.cursor()
    query = '''
        SELECT t1.id, t1.content, t1.answer, t1.modified, IFNULL(t2.name, 'NULL')
        FROM t_todo t1
        LEFT JOIN t_topic t2
        ON t1.topic_id = t2.id
        WHERE t1.status = 1 ORDER BY modified
    '''
    cursor.execute(query)
    print("work have done:")
    t = int(getMonStartTime())
    flag = False
    for (id, content, answer, modified, topic) in cursor:
        if(not flag and int(modified.timestamp()) > t):
            print("    DONE THIS WEEK:")
            flag = not flag
        answer = answer.replace('\n', '\n' + ' ' * 8)
        content = content.replace('\n', '\n' + ' ' * 8)
        print(" " * 4 + "{}: {}\n        {}".format(id, topic, content))
        print("        {}".format(answer))
    cursor.close()

def add_todo(conn):
    cursor = conn.cursor()
    EDITOR = os.environ.get('EDITOR','vim')
    file_name = '/tmp/question';
    cursor.execute('SELECT id FROM t_topic WHERE current = 1')
    current_topic_id = 0
    for topic_id, in cursor:
        current_topic_id = topic_id
    subprocess.call([EDITOR, file_name])
    with open(file_name, 'r') as f:
        question = f.read()
    if len(question.strip()) <= 0:
        return
    insert = "INSERT INTO t_todo (content, topic_id) VALUES ('{}', {})".format(question, current_topic_id)
    cursor.execute(insert)
    print("add todo success")
    conn.commit()
    cursor.close()

def add_trifles(conn):
    cursor = conn.cursor()
    EDITOR = os.environ.get('EDITOR','vim')
    file_name = '/tmp/trifiles';
    subprocess.call([EDITOR, file_name])
    with open(file_name, 'r') as f:
        content = f.read()
    if len(content.strip()) <= 0:
        return
    insert = "INSERT INTO t_trifles (content) VALUES('{}')".format(content)
    cursor.execute(insert)
    print("add trifles success")
    conn.commit()
    cursor.close()

def edit_todo(conn, edit_id):
    EDITOR = os.environ.get('EDITOR','vim')
    file_name = '/tmp/question';
    cursor = conn.cursor()
    query_content = "SELECT content FROM t_todo WHERE id = {}".format(edit_id)
    cursor.execute(query_content)
    with open(file_name, 'w') as f:
        for content, in cursor:
            f.write(content)
    subprocess.call([EDITOR, file_name])
    with open(file_name, 'r') as f:
        question = f.read()
    if len(question.strip()) <= 0:
        return
    update = "UPDATE t_todo SET content = '{}' WHERE id = {}".format(question, edit_id)
    cursor.execute(update)
    print("edit todo success")
    conn.commit()
    cursor.close()

def kill_todo(conn, kill):
    EDITOR = os.environ.get('EDITOR','vim')
    file_name = '/tmp/answer';
    subprocess.call([EDITOR, file_name])
    with open(file_name, 'r') as f:
        answer = f.read()
    cursor = conn.cursor()
    update = ("UPDATE t_todo SET status = 1, answer = '{}' WHERE id = {}".format(answer, kill))
    cursor.execute(update)
    conn.commit()
    print("kill todo success")
    # subprocess.getoutput("sed -ie '2,$d' /tmp/answer")
    cursor.close()

def list_topic(conn):
    cursor = conn.cursor()
    query = "SELECT name, current FROM t_topic WHERE enable = 1"
    cursor.execute(query)
    for topic, current in cursor:
        if current == 1:
            print("{}(current)".format(topic))
        else:
            print(topic)
    cursor.close()

def create_topic(conn, topic):
    cursor = conn.cursor()
    insert = "INSERT INTO t_topic (name) VALUES ('{}')".format(topic)
    cursor.execute(insert)
    conn.commit()
    cursor.close()

def switch_topic(conn, topic):
    cursor = conn.cursor()
    cursor.execute('UPDATE t_topic SET current = 0')
    cursor.execute('UPDATE t_topic SET current = 1 WHERE name = "{}"'.format(topic))
    conn.commit()
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



