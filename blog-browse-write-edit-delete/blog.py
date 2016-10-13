# Blog Flask application

import os
import sqlite3
from flask import Flask, request, render_template, g

# Create the application
app = Flask(__name__)

####################################################
# Routes

@app.route("/")
def homepage():
    return render_template("home.html")

@app.route("/dump")
def dump_entries():
    db = get_db()
    rows = db.execute('select id, date, title, content from entries order by date')
    output = ""
    for r in rows:
        debug(str(dict(r)))
        output += str(dict(r))
        output += "\n"
    return "<pre>" + output + "</pre>"
    
@app.route("/browse")
def browse():
    db = get_db()
    rows = db.execute('select id, date, title, content from entries order by date')
    rowlist = rows.fetchall()
    return render_template('browse.html', entries=rowlist)
    
@app.route("/write", methods=['get', 'post'])
def write():
    # Step 1, display form
    if "step" not in request.form:     
        return render_template('write.html', step="compose_entry")
    
    # Step 2, add blog post to database.
    elif request.form["step"] == "add_entry":
        db = get_db()
        db.execute("insert into entries (date, title, content) values (datetime('now'), ?, ?)",
                   [request.form['title'], request.form['content']])
        db.commit()
        return render_template("write.html", step="add_entry")
        
@app.route("/edit", methods=['get', 'post'])
def edit():
    debug("form data=" + str(request.form))
    # Step 1, display form to select which entry to edit
    if "step" not in request.form:
        db = get_db()
        rows = db.execute('select id, date, title, content from entries order by date')
        rowlist = rows.fetchall()
        return render_template('edit.html', step="display_entries", entries=rowlist)
    
    # Step 2, get postID from form, SELECT this post from the db, and display
    # a form to edit that post.
    elif request.form["step"] == "make_edits":
        db = get_db()
        # get the postID from the form
        postid = int(request.form["postid"])
        debug("Using postid=" + str(postid))
        
        # query the DB to retrieve that post by ID.  We use fetchone()
        # to retrieve the only row (there can be only one!)
        row = db.execute("select id, date, title, content from entries where id=?", [postid])
        therow = row.fetchone()
        debug("db retrieved: " + str(dict(therow)))
        
        return render_template("edit.html", step="make_edits", entry=therow)
        
    # Step 3, user has changed post, now update the DB with changes
    elif request.form["step"] == "update_database":
        db = get_db()
        
        # get the postID from the form
        postid = int(request.form["postid"])
        
        # figure out if we update the date
        if "changedate" in request.form:
            changedate = True
        else:
            changedate = False
        
        # run our UPDATE
        if changedate:
            db.execute("update entries set title=?, content=?, date=datetime('now') where id=?",
                       [request.form['title'], request.form['content'], postid])
        else:
            db.execute("update entries set title=?, content=? where id=?", 
                       [request.form['title'], request.form['content'], postid])
        db.commit()
        return render_template("edit.html", step="update_database")
        
@app.route("/delete", methods=['get', 'post'])
def delete():
    debug("form data=" + str(request.form))
    
    # Step 1, display form to select which entry to delete
    if "step" not in request.form:
        db = get_db()
        rows = db.execute('select id, date, title, content from entries order by date')
        rowlist = rows.fetchall()
        return render_template('delete.html', step="display_entries", entries=rowlist)
        
    # Step 2, user has changed post, now update the DB with changes
    elif request.form["step"] == "delete_entry":
        db = get_db()
        
        # get the postID from the form
        postid = int(request.form["postid"])
        
        # run our DELETE
        db.execute("delete from entries where id=?", [postid])
        db.commit()
        return render_template("delete.html", step="delete_entry")
    

#####################################################
# Database handling 
  
def connect_db():
    """Connects to the database."""
    debug("Connecting to DB.")
    conn = sqlite3.connect(os.path.join(app.root_path, 'blog.db'))
    conn.row_factory = sqlite3.Row
    return conn
    
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db_connection'):
        g.db_connection = connect_db()
    return g.db_connection
    
@app.teardown_appcontext
def close_db(error):
    """Closes the database automatically when the application
    context ends."""
    debug("Disconnecting from DB.")
    if hasattr(g, 'db_connection'):
        g.db_connection.close()

######################################################
# Command line utilities 
        
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def init_db_command():
    """Initializes the database."""
    print("Initializing DB.")
    init_db()
    
def populate_db():
    db = get_db()
    with app.open_resource('populate.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('populate')
def populate_db_command():
    """Populates the database with sample data."""
    print("Populating DB with sample data.")
    populate_db()
    
    
#####################################################
# Debugging

def debug(s):
    """Prints a message to the screen (not web browser) 
    if FLASK_DEBUG is set."""
    if app.config['DEBUG']:
        print(s)
