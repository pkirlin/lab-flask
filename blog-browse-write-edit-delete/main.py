# Blog Flask application

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g, current_app
from flask.cli import with_appcontext
import click

# initialize Flask
app = Flask(__name__)

####################################################
# Routes

@app.route("/")
def homepage():
    return render_template("home.html")

@app.route("/dump")
def dump_entries():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('select id, date, title, content from entries order by date')
    rows = cursor.fetchall()
    output = ""
    for r in rows:
        debug(str(dict(r)))
        output += str(dict(r))
        output += "\n"
    return "<pre>" + output + "</pre>"

@app.route("/browse")
def browse():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('select id, date, title, content from entries order by date')
    rowlist = cursor.fetchall()
    return render_template('browse.html', entries=rowlist)

@app.route("/write", methods=['get', 'post'])
def write():
    # Step 1, display form
    if "step" not in request.form:     
        return render_template('write.html', step="compose_entry")
    
    # Step 2, add blog post to database.
    elif request.form["step"] == "add_entry":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("insert into entries (title, content) values (%s, %s)",
                   [request.form['title'], request.form['content']])
        conn.commit()
        return render_template("write.html", step="add_entry")

@app.route("/edit", methods=['get', 'post'])
def edit():
    debug("form data=" + str(request.form))
    # Step 1, display form to select which entry to edit
    if "step" not in request.form:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('select id, date, title, content from entries order by date')
        rowlist = cursor.fetchall()
        return render_template('edit.html', step="display_entries", entries=rowlist)
    
    # Step 2, get postID from form, SELECT this post from the db, and display
    # a form to edit that post.    
    elif request.form["step"] == "make_edits":
        conn = get_db()
        cursor = conn.cursor()
        # get the postID from the form
        postid = int(request.form["postid"])
        debug("Using postid=" + str(postid))
        
        # query the DB to retrieve that post by ID.  We use fetchone()
        # to retrieve the only row (there can be only one!)
        cursor.execute("select id, date, title, content from entries where id=%s", [postid])
        row = cursor.fetchone()
        debug("db retrieved: " + str(dict(row)))
        
        return render_template("edit.html", step="make_edits", entry=row)
        
    # Step 3, user has changed post, now update the DB with changes
    elif request.form["step"] == "update_database":
        conn = get_db()
        cursor = conn.cursor()
        
        # get the postID from the form
        postid = int(request.form["postid"])
        
        # figure out if we update the date
        if "changedate" in request.form:
            changedate = True
        else:
            changedate = False
        
        # run our UPDATE
        if changedate:
            cursor.execute("update entries set title=%s, content=%s, date=now() where id=%s",
                       [request.form['title'], request.form['content'], postid])
        else:
            cursor.execute("update entries set title=%s, content=%s where id=%s", 
                       [request.form['title'], request.form['content'], postid])
        conn.commit()
        return render_template("edit.html", step="update_database")

@app.route("/delete", methods=['get', 'post'])
def delete():
    debug("form data=" + str(request.form))
    
    # Step 1, display form to select which entry to delete
    if "step" not in request.form:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('select id, date, title, content from entries order by date')
        rowlist = cursor.fetchall()
        return render_template('delete.html', step="display_entries", entries=rowlist)
        
    # Step 2, user has changed post, now update the DB with changes
    elif request.form["step"] == "delete_entry":
        conn = get_db()
        cursor = conn.cursor()
        
        # get the postID from the form
        postid = int(request.form["postid"])
        
        # run our DELETE
        cursor.execute("delete from entries where id=%s", [postid])
        conn.commit()
        return render_template("delete.html", step="delete_entry")

def dump_entries():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("select * from entries")
    rows = cur.fetchall()
    print("Here are the entries:")
    print(rows)
    

#####################################################
# Database handling 
  
def connect_db():
    """Connects to the database."""
    debug("Connecting to DB.")
    conn = psycopg2.connect(host="database.rhodescs.org", user="sample", password="sample", dbname="practice", 
        cursor_factory=psycopg2.extras.DictCursor)
    return conn
    
def get_db():
    """Retrieve the database connection or initialize it. The connection
    is unique for each request and will be reused if this is called again.
    """
    if "db" not in g:
        g.db = connect_db()

    return g.db
    
@app.teardown_appcontext
def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()
        debug("Closing DB")

@app.cli.command("initdb")
def init_db():
    """Clear existing data and create new tables."""
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("schema.sql") as file: # open the file
        alltext = file.read() # read all the text
        cur.execute(alltext) # execute all the SQL in the file
    conn.commit()
    print("Initialized the database.")

@app.cli.command('populate')
def populate_db():
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("populate.sql") as file: # open the file
        alltext = file.read() # read all the text
        cur.execute(alltext) # execute all the SQL in the file
    conn.commit()
    print("Populated DB with sample data.")
    dump_entries()

#def init_app(app):
#    """Register database functions with the Flask app. This is called by
#    the application factory.
#    """
#    app.teardown_appcontext(close_db)
#    app.cli.add_command(init_db_command)
    
    
#####################################################
# Debugging

def debug(s):
    """Prints a message to the screen (not web browser) 
    if FLASK_DEBUG is set."""
    if app.config['DEBUG']:
        print(s)

########## Start running

# Create the application
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
