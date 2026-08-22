
import os, json, secrets, sqlite3, re, uuid
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "elroi.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config.update(
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)

STATUSES = [
    ("preparing", "Preparing"),
    ("almost_done", "Almost Done"),
    ("collect_now", "Collect Now"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]
CATEGORIES = ["Sphatlo / Kota", "Box Specials", "Club Specials", "Burgers", "Toasted Sandwich", "Pap", "Rice", "Ice Cream"]

PRODUCTS = [
("Sphatlo / Kota","Normal QL","Polony, Chips & Steak + gravy",15),
("Sphatlo / Kota","Cheese QL","Polony, Chips & Steak gravy",20),
("Sphatlo / Kota","Egg QL","Polony, Chips & Steak gravy",20),
("Sphatlo / Kota","Egg & Cheese","Polony, Egg & Cheese, Steak gravy",25),
("Sphatlo / Kota","Steak QL","Steak, Polony, Cheese & Steak gravy",45),
("Sphatlo / Kota","Party Cheese","Steak, cheese, Polony, Steak & gravy",45),
("Sphatlo / Kota","Russian QL","Russian, Polony, Chips, & steak gravy",40),
("Sphatlo / Kota","Russian & Cheese","Russian, Polony, Chips and Steak gravy",45),
("Sphatlo / Kota","Elroi QL","Chips, Patty, Polony, Cheese, Egg, Russian, Steak, steak gravy",60),
("Box Specials","Small Chips","",15),
("Box Specials","Medium Chips","",25),
("Box Specials","Large Chips","",30),
("Box Specials","Extra Large Chips","",40),
("Box Specials","Polony & Chips","",30),
("Box Specials","Polony & Chips","",50),
("Box Specials","Russian & Chips","",15),
("Box Specials","Vienna & Chips","",15),
("Box Specials","Sausage & Chips","",15),
("Box Specials","Boerewors & Chips","",45),
("Box Specials","1/4 Chicken & Chips","",40),
("Box Specials","Half Chicken & Chips","",70),
("Box Specials","Full Chicken & Chips","",120),
("Box Specials","Steak & Chips","",70),
("Club Specials","Small Club Special","Medium Chips, Polony, Steak and Gravy Sausage",60),
("Club Specials","Large Club Special","Large Chips, Polony, Steak, Sausages, Gravy",120),
("Club Specials","Breakfast","2 eggs, Vienna, 1 sausage, chips, 2 slices of toast, fried tomatoes, T bone & chips or pap",60),
("Burgers","Normal Chips Burger","2 slices of bread, Chips & Steak Gravy",12),
("Burgers","Chip Burger With Cheese","2 slices, Chips & Cheese & Steak Gravy",15),
("Burgers","Chip Burger Special","2 slices, Chips, Polony & Cheese, Steak Gravy",20),
("Burgers","Burger Plain","Patty, Lettuce, Onion, Tomato",30),
("Burgers","Cheese Burger","Patty, Cheese, Lettuce, Onion, Tomato",35),
("Burgers","Burger Special","Patty, Cheese, Polony, Lettuce, Onion, Tomato & Chips",40),
("Toasted Sandwich","Daywood","Patty, Polony, Cheese, Egg, Russian",50),
("Toasted Sandwich","Toasted Steak Special","Steak, Cheese, Polony & Chips on the side",50),
("Toasted Sandwich","Toasted Steak, Cheese & Chips","",45),
("Toasted Sandwich","Plain Toasted","Steak and Chips",40),
("Pap","Pap + T-Bone + All Salad","",70),
("Pap","Pap + Steak + All Salas","",70),
("Pap","Pap + Beef stew + All Salad","",50),
("Pap","Pap + Boerewors + All Salad","",45),
("Pap","Pap + Quarter Chicken + All Salad","",40),
("Pap","Pap + 1/2 Grilled Chicken + All Salad","",60),
("Pap","Pap + Full Grilled Chicken + All Salad","",120),
("Pap","Pap + Steak & Wors + All Salad","",110),
("Pap","Pap + Steak + Wors + Chicken + All Salad","",150),
("Rice","Rice + Beef stew + All Salad","",50),
("Rice","Rice + 1/4 Grilled Chicken + All Salad","",40),
("Rice","Rice + 1/5 Grilled Chicken + All Salad","",60),
("Rice","Rice + Full Grilled Chicken + All Salad","",120),
("Rice","Rice + Steak + All Salad","",70),
("Ice Cream","Cone","",9),
("Ice Cream","Cup","",11),
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('admin','creator')),
      active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      category TEXT NOT NULL,
      name TEXT NOT NULL,
      description TEXT DEFAULT '',
      price REAL NOT NULL,
      image TEXT DEFAULT '',
      remove_options TEXT DEFAULT '',
      add_options TEXT DEFAULT '',
      active INTEGER NOT NULL DEFAULT 1,
      sort_order INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_no TEXT UNIQUE NOT NULL,
      customer_name TEXT NOT NULL,
      phone TEXT NOT NULL,
      email TEXT DEFAULT '',
      method TEXT NOT NULL,
      payment_status TEXT NOT NULL DEFAULT 'pending',
      status TEXT NOT NULL DEFAULT 'preparing',
      total REAL NOT NULL,
      notes TEXT DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL,
      product_id INTEGER,
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      qty INTEGER NOT NULL,
      unit_price REAL NOT NULL,
      removals TEXT DEFAULT '',
      additions TEXT DEFAULT '',
      special_note TEXT DEFAULT '',
      FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
    );
    """)
    # Default accounts can be changed from Creator dashboard.
    if not c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone():
        c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                  ("admin", generate_password_hash("ElroiAdmin123!"), "admin"))
    if not c.execute("SELECT 1 FROM users WHERE role='creator' LIMIT 1").fetchone():
        c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                  ("creator", generate_password_hash("ElroiCreator123!"), "creator"))
    defaults = {
        "shop_name":"ELROI FAST FOOD",
        "tagline":"Good Food, Good Mood",
        "whatsapp":"+27643981061",
        "contact":"069 1660 040",
        "maintenance":"0",
        "delivery":"coming_soon",
        "card_payment_url":"",
        "card_payment_label":"Pay securely by card before collection",
    }
    for k,v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        for i,(cat,name,desc,price) in enumerate(PRODUCTS):
            # Helpful default customization choices. Admin can change them per product.
            removes = "Onion, Tomato, Cheese, Polony, Egg, Russian, Chips, Gravy, Salad"
            adds = "Extra Cheese:5, Extra Egg:5, Extra Polony:7, Extra Chips:10, Extra Gravy:3"
            if "Chips" in name and "Ice Cream" not in cat:
                adds = "Extra Chips:10, Extra Cheese:5, Extra Gravy:3"
            c.execute("""INSERT INTO products(category,name,description,price,remove_options,add_options,sort_order)
                         VALUES(?,?,?,?,?,?,?)""",(cat,name,desc,price,removes,adds,i))
    c.commit(); c.close()

def get_settings():
    c=db(); rows=c.execute("SELECT key,value FROM settings").fetchall(); c.close()
    return {r["key"]:r["value"] for r in rows}

def setting(key, default=""):
    return get_settings().get(key, default)

@app.context_processor
def inject_globals():
    return {"settings": get_settings(), "statuses": STATUSES, "categories": CATEGORIES}

@app.before_request
def site_guard():
    init_db()
    path=request.path
    if path.startswith("/static/") or path.startswith("/admin") or path.startswith("/creator") or path.startswith("/login") or path.startswith("/logout"):
        return
    if setting("maintenance","0") == "1":
        return render_template("maintenance.html"), 503

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login", next=request.path))
            if role and session.get("role") != role:
                return "Forbidden", 403
            return fn(*args, **kwargs)
        return wrapper
    return deco

def csrf():
    token=session.get("_csrf")
    if not token:
        token=secrets.token_urlsafe(24); session["_csrf"]=token
    return token

@app.context_processor
def csrf_context():
    return {"csrf_token": csrf()}

def check_csrf():
    token = request.form.get("_csrf")
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        token = payload.get("_csrf")
    if token != session.get("_csrf"):
        abort(400, "Invalid form token")

def parse_adds(s):
    result=[]
    for part in (s or "").split(","):
        part=part.strip()
        if not part: continue
        if ":" in part:
            name, price = part.rsplit(":",1)
            try: price=float(price.strip())
            except: price=0
            result.append({"name":name.strip(),"price":price})
        else:
            result.append({"name":part,"price":0})
    return result

def parse_removes(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]

def money(x):
    return f"R{x:,.2f}"

def clean_phone(p):
    return re.sub(r"[^\d+]","",p or "")

def make_order_no():
    while True:
        n="ELR-"+datetime.now().strftime("%y%m%d")+"-"+secrets.token_hex(2).upper()
        c=db(); exists=c.execute("SELECT 1 FROM orders WHERE order_no=?",(n,)).fetchone(); c.close()
        if not exists: return n

@app.route("/")
def index():
    c=db(); products=c.execute("SELECT * FROM products WHERE active=1 ORDER BY sort_order,id").fetchall(); c.close()
    grouped={cat:[] for cat in CATEGORIES}
    for p in products: grouped.setdefault(p["category"],[]).append(p)
    return render_template("index.html", grouped=grouped, parse_adds=parse_adds, parse_removes=parse_removes)

@app.route("/api/product/<int:pid>")
def product_api(pid):
    c=db(); p=c.execute("SELECT * FROM products WHERE id=? AND active=1",(pid,)).fetchone(); c.close()
    if not p: return jsonify({"error":"not found"}),404
    d=dict(p); d["add_options"]=parse_adds(d["add_options"]); d["remove_options"]=parse_removes(d["remove_options"])
    return jsonify(d)

@app.route("/checkout", methods=["GET","POST"])
def checkout():
    if request.method=="GET":
        return render_template("checkout.html")
    check_csrf()
    try:
        data=request.get_json(silent=True) if request.is_json else request.form
        items=json.loads(data.get("items","[]")) if isinstance(data.get("items"),str) else data.get("items",[])
        if not items: return jsonify({"ok":False,"error":"Your cart is empty."}),400
        name=(data.get("customer_name") or "").strip()
        phone=clean_phone(data.get("phone") or "")
        method=(data.get("method") or "cash").strip()
        if not name or len(phone)<7: return jsonify({"ok":False,"error":"Enter your name and a valid phone number."}),400
        if method not in ("cash","card"): return jsonify({"ok":False,"error":"Invalid collection method."}),400
        c=db(); total=0; valid=[]
        for it in items:
            pid=int(it.get("product_id",0)); qty=max(1,min(int(it.get("qty",1)),50))
            p=c.execute("SELECT * FROM products WHERE id=? AND active=1",(pid,)).fetchone()
            if not p: continue
            adds=it.get("additions") or []; rems=it.get("removals") or []
            add_total=0; add_names=[]
            available_adds={a["name"]:a["price"] for a in parse_adds(p["add_options"])}
            available_rems=set(parse_removes(p["remove_options"]))
            for a in adds:
                an=str(a.get("name",""))
                if an in available_adds:
                    add_total += available_adds[an]; add_names.append(an)
            rem_names=[str(r) for r in rems if str(r) in available_rems]
            unit=p["price"]+add_total
            total += unit*qty
            valid.append((p,qty,unit,", ".join(rem_names),", ".join(add_names),str(it.get("special_note",""))[:250]))
        if not valid: return jsonify({"ok":False,"error":"No valid products in your cart."}),400
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"); order_no=make_order_no()
        notes=str(data.get("notes",""))[:500]
        pay="pending" if method=="card" else "cash_on_collection"
        cur=c.cursor()
        cur.execute("""INSERT INTO orders(order_no,customer_name,phone,email,method,payment_status,status,total,notes,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (order_no,name,phone,str(data.get("email",""))[:120],method,pay,"preparing",total,notes,now,now))
        oid=cur.lastrowid
        for p,qty,unit,rems,adds,note in valid:
            cur.execute("""INSERT INTO order_items(order_id,product_id,name,category,qty,unit_price,removals,additions,special_note)
                           VALUES(?,?,?,?,?,?,?,?,?)""",(oid,p["id"],p["name"],p["category"],qty,unit,rems,adds,note))
        c.commit(); c.close()
        payment_url=setting("card_payment_url","").strip() if method=="card" else ""
        return jsonify({"ok":True,"order_no":order_no,"total":total,"payment_url":payment_url,
                        "whatsapp":setting("whatsapp","+27643981061"),
                        "message":f"ELROI order {order_no} placed. Total R{total:.2f}. Collection: {'CARD' if method=='card' else 'CASH'}."})
    except Exception as e:
        return jsonify({"ok":False,"error":"Could not place the order. Please try again."}),500

@app.route("/track/<order_no>")
def track(order_no):
    c=db(); order=c.execute("SELECT * FROM orders WHERE order_no=?",(order_no.upper(),)).fetchone()
    items=c.execute("SELECT * FROM order_items WHERE order_id=(SELECT id FROM orders WHERE order_no=?)",(order_no.upper(),)).fetchall() if order else []
    c.close()
    if not order: return render_template("track.html", order=None, items=[]),404
    return render_template("track.html", order=order, items=items)

@app.route("/status/<order_no>")
def status_api(order_no):
    c=db(); o=c.execute("SELECT order_no,status,payment_status,total,updated_at FROM orders WHERE order_no=?",(order_no.upper(),)).fetchone(); c.close()
    if not o: return jsonify({"ok":False}),404
    return jsonify({"ok":True,**dict(o)})

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        check_csrf(); username=request.form.get("username","").strip()
        c=db(); u=c.execute("SELECT * FROM users WHERE username=? AND active=1",(username,)).fetchone(); c.close()
        if u and check_password_hash(u["password_hash"],request.form.get("password","")):
            session.clear(); session["user_id"]=u["id"]; session["role"]=u["role"]; session["username"]=u["username"]; session["_csrf"]=secrets.token_urlsafe(24)
            nxt=request.args.get("next") or (url_for("creator_dashboard") if u["role"]=="creator" else url_for("admin_dashboard"))
            return redirect(nxt)
        flash("Incorrect username or password.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    c=db()
    orders=c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 100").fetchall()
    products=c.execute("SELECT * FROM products ORDER BY sort_order,id").fetchall()
    stats={
        "orders":c.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"],
        "pending":c.execute("SELECT COUNT(*) n FROM orders WHERE status IN ('preparing','almost_done')").fetchone()["n"],
        "sales":c.execute("SELECT COALESCE(SUM(total),0) n FROM orders WHERE status!='cancelled'").fetchone()["n"],
    }
    c.close()
    return render_template("admin.html",orders=orders,products=products,stats=stats)

@app.route("/admin/order/<int:oid>/status", methods=["POST"])
@login_required("admin")
def admin_order_status(oid):
    check_csrf(); status=request.form.get("status")
    payment=request.form.get("payment_status")
    if status not in dict(STATUSES): return "Invalid status",400
    c=db(); c.execute("UPDATE orders SET status=?,payment_status=?,updated_at=? WHERE id=?",
                      (status,payment or "pending",datetime.now().strftime("%Y-%m-%d %H:%M:%S"),oid)); c.commit(); c.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/product/save", methods=["POST"])
@login_required("admin")
def admin_product_save():
    check_csrf()
    pid=request.form.get("id")
    fields=(request.form.get("category","Sphatlo / Kota"),request.form.get("name","").strip(),request.form.get("description","").strip(),
            float(request.form.get("price","0") or 0),request.form.get("remove_options",""),request.form.get("add_options",""),
            1 if request.form.get("active")=="1" else 0,int(request.form.get("sort_order","0") or 0))
    c=db()
    if pid:
        c.execute("""UPDATE products SET category=?,name=?,description=?,price=?,remove_options=?,add_options=?,active=?,sort_order=? WHERE id=?""",fields+(int(pid),))
    else:
        c.execute("""INSERT INTO products(category,name,description,price,remove_options,add_options,active,sort_order)
                     VALUES(?,?,?,?,?,?,?,?)""",fields)
    c.commit(); c.close(); return redirect(url_for("admin_dashboard"))

@app.route("/admin/product/<int:pid>/delete", methods=["POST"])
@login_required("admin")
def admin_product_delete(pid):
    check_csrf(); c=db(); c.execute("UPDATE products SET active=0 WHERE id=?",(pid,)); c.commit(); c.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/product/<int:pid>/image", methods=["POST"])
@login_required("admin")
def admin_product_image(pid):
    check_csrf(); f=request.files.get("image")
    if not f or not f.filename: return redirect(url_for("admin_dashboard"))
    ext=os.path.splitext(secure_filename(f.filename))[1].lower()
    if ext not in {".jpg",".jpeg",".png",".webp"}: flash("Only JPG, PNG or WEBP images are allowed.","error"); return redirect(url_for("admin_dashboard"))
    name=f"product_{pid}_{uuid.uuid4().hex[:10]}{ext}"; f.save(os.path.join(UPLOAD_DIR,name))
    c=db(); old=c.execute("SELECT image FROM products WHERE id=?",(pid,)).fetchone()
    c.execute("UPDATE products SET image=? WHERE id=?",(name,pid)); c.commit(); c.close()
    if old and old["image"]:
        try: os.remove(os.path.join(UPLOAD_DIR,old["image"]))
        except OSError: pass
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/product/<int:pid>/image/delete", methods=["POST"])
@login_required("admin")
def admin_product_image_delete(pid):
    check_csrf(); c=db(); p=c.execute("SELECT image FROM products WHERE id=?",(pid,)).fetchone()
    c.execute("UPDATE products SET image='' WHERE id=?",(pid,)); c.commit(); c.close()
    if p and p["image"]:
        try: os.remove(os.path.join(UPLOAD_DIR,p["image"]))
        except OSError: pass
    return redirect(url_for("admin_dashboard"))

@app.route("/creator")
@login_required("creator")
def creator_dashboard():
    c=db(); users=c.execute("SELECT id,username,role,active FROM users ORDER BY role").fetchall(); c.close()
    return render_template("creator.html", users=users)

@app.route("/creator/settings", methods=["POST"])
@login_required("creator")
def creator_settings():
    check_csrf()
    allowed=["shop_name","tagline","whatsapp","contact","maintenance","card_payment_url","card_payment_label"]
    c=db()
    for k in allowed:
        if k in request.form:
            v=request.form.get(k,"").strip()
            if k=="whatsapp": v=clean_phone(v)
            c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,v))
    c.commit(); c.close(); return redirect(url_for("creator_dashboard"))

@app.route("/creator/user", methods=["POST"])
@login_required("creator")
def creator_user():
    check_csrf()
    uid=request.form.get("id"); username=request.form.get("username","").strip(); password=request.form.get("password","")
    role=request.form.get("role","admin")
    if role not in ("admin","creator") or not username: return redirect(url_for("creator_dashboard"))
    c=db()
    try:
        if uid:
            if password:
                c.execute("UPDATE users SET username=?,password_hash=?,role=? WHERE id=?",(username,generate_password_hash(password),role,int(uid)))
            else:
                c.execute("UPDATE users SET username=?,role=? WHERE id=?",(username,role,int(uid)))
        else:
            c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",(username,generate_password_hash(password or secrets.token_urlsafe(10)),role))
        c.commit()
    except sqlite3.IntegrityError:
        flash("That username already exists.","error")
    c.close(); return redirect(url_for("creator_dashboard"))

@app.route("/creator/user/<int:uid>/toggle", methods=["POST"])
@login_required("creator")
def creator_user_toggle(uid):
    check_csrf(); c=db(); c.execute("UPDATE users SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?",(uid,)); c.commit(); c.close()
    return redirect(url_for("creator_dashboard"))

@app.route("/scan")
@login_required("admin")
def scan():
    return render_template("scan.html")

@app.route("/health")
def health(): return "OK",200

if __name__=="__main__":
    init_db()
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port,debug=False)
