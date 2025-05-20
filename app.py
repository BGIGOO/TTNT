import osmnx as ox
from flask_cors import CORS
from flask import Flask, render_template, request, redirect, url_for
from flask import (Flask, request, jsonify, send_from_directory,
                   render_template, redirect, url_for, session, flash)
import os # Cần cho secret_key
from functools import wraps # Để tạo decorator yêu cầu đăng nhập
# Import các hàm từ module pathfinding
from core_logic.pathfinding import heuristic1, heuristic2, heuristic3, heuristic4, astar_path_custom, Dijkstra, find_nearest_node_haversine
from geopy.geocoders import Nominatim

app = Flask(__name__)
CORS(app)

# Cấu hình khóa bí mật cho session
# Trong môi trường production, nên đặt giá trị này từ biến môi trường
app.secret_key = os.urandom(24) # Hoặc một chuỗi ngẫu nhiên cố định
geolocator = Nominatim(user_agent="phan mem tim duong di")

#khoi tao du lieu tai khoan demo
users_db = {
    "manh": {"password": "1", "email": "user1@example.com"},
    "user2": {"password": "password2", "email": "user2@example.com"}
}

print("Đang tải bản đồ đường phố...")
G = ox.graph_from_point((10.848015315160042, 106.78667009709487), dist=1000, network_type='drive', simplify=True)
print("Tải bản đồ xong.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in_user' not in session:
            flash("Bạn cần đăng nhập để truy cập trang này.", "warning")
            return redirect(url_for('show_login_form'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'logged_in_user' in session:
        return redirect(url_for('map_page'))
    return redirect(url_for('show_login_form'))

@app.route('/login', methods=['GET', 'POST'])
def show_login_form():
    if request.method == 'POST':
        # Xử lý dữ liệu JSON từ frontend
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"success": False, "message": "Vui lòng nhập tên đăng nhập và mật khẩu."}), 400

        user = users_db.get(username)
        # So sánh mật khẩu (trong thực tế, so sánh hash)
        if user and user['password'] == password:
            session['logged_in_user'] = username
            # flash(f"Chào mừng {username}!", "success") # flash hoạt động với render_template
            return jsonify({"success": True, "message": "Đăng nhập thành công!"})
        else:
            return jsonify({"success": False, "message": "Tên đăng nhập hoặc mật khẩu không đúng."}), 401
    
    # Nếu là GET request, hoặc đã đăng nhập thì chuyển hướng
    if 'logged_in_user' in session:
        return redirect(url_for('map_page'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email') # Email có thể tùy chọn

    if not username or not password:
        return jsonify({"success": False, "message": "Tên đăng nhập và mật khẩu không được để trống."}), 400
    
    if username in users_db:
        return jsonify({"success": False, "message": "Tên đăng nhập đã tồn tại."}), 409
    
    # Trong thực tế: hash mật khẩu trước khi lưu
    users_db[username] = {"password": password, "email": email}
    print(f"Người dùng mới đăng ký: {username}, Cơ sở dữ liệu người dùng hiện tại: {users_db}") # Log để kiểm tra
    return jsonify({"success": True, "message": "Đăng ký thành công! Vui lòng đăng nhập."}), 201

@app.route('/logout')
@login_required # Đảm bảo người dùng đã đăng nhập mới có thể logout
def logout():
    session.pop('logged_in_user', None)
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('show_login_form'))

# --- Routes cho ứng dụng bản đồ (yêu cầu đăng nhập) ---
@app.route('/map')
@login_required
def map_page():
    return render_template('map_page.html', username=session.get('logged_in_user'))


@app.route('/route')
def get_route():
    orig_lat = float(request.args.get('orig_lat'))
    orig_lon = float(request.args.get('orig_lon'))
    dest_lat = float(request.args.get('dest_lat'))
    dest_lon = float(request.args.get('dest_lon'))

    orig_node = find_nearest_node_haversine(G, orig_lon, orig_lat)
    dest_node = find_nearest_node_haversine(G, dest_lon, dest_lat)

    # Tìm đường bằng A*
    route = astar_path_custom(G, orig_node, dest_node, heuristic_func=heuristic4, weight='length')
    # route = Dijkstra(G, orig_node, dest_node, heuristic_func=heuristic1, weight='length')

    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]

    # print("\nĐây: ",orig_node," va ",dest_node,"\n")
    # print("\nĐây là : ",route,"\n")
    # print("\nĐây là ds node: ",route_coords,"\n")
    
    return jsonify({'route': route_coords})

if __name__ == '__main__':
    app.run(debug=True)
