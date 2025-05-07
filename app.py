import osmnx as ox
from flask import (Flask, request, jsonify, send_from_directory,
                   render_template, redirect, url_for, session, flash)
from flask_cors import CORS
import os # Cần cho secret_key
from functools import wraps # Để tạo decorator yêu cầu đăng nhập

# Import các hàm từ module pathfinding
from core_logic.pathfinding import heuristic, astar_path_custom, find_nearest_node_haversine

# Khởi tạo ứng dụng Flask
# Flask sẽ tự động tìm thư mục 'templates' và 'static' cùng cấp với app.py
app = Flask(__name__)
CORS(app) # Cho phép CORS nếu frontend và backend khác domain/port khi phát triển

# Cấu hình khóa bí mật cho session
# Trong môi trường production, bạn nên đặt giá trị này từ biến môi trường
app.secret_key = os.urandom(24) # Hoặc một chuỗi ngẫu nhiên cố định

# --- "Cơ sở dữ liệu" người dùng mô phỏng ---
# Trong thực tế, bạn sẽ dùng database (SQLAlchemy, MongoDB, ...) và hash mật khẩu
users_db = {
    "user1": {"password": "password1", "email": "user1@example.com"},
    "user2": {"password": "password2", "email": "user2@example.com"}
}
# Lưu ý: Đây chỉ là mô phỏng, KHÔNG BAO GIỜ lưu mật khẩu dạng plain text trong ứng dụng thực tế.
# Hãy sử dụng các thư viện như Werkzeug để hash mật khẩu.

# --- Tải đồ thị ---
GRAPH_LOADED_SUCCESSFULLY = False
G = None
try:
    print("Đang tải bản đồ đường phố...")
    # Sử dụng một điểm cụ thể ở TP.HCM và bán kính nhỏ hơn để tải nhanh hơn khi test
    # G = ox.graph_from_point((10.7769, 106.7009), dist=2000, network_type='drive', simplify=True)
    # Giữ lại cấu hình cũ của bạn:
    G = ox.graph_from_point((10.847874, 106.791798), dist=3000, network_type='drive_service', simplify=True)
    print("Tải bản đồ xong.")
    GRAPH_LOADED_SUCCESSFULLY = True
except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể tải bản đồ: {e}")
    print("Ứng dụng có thể không hoạt động đúng với các chức năng liên quan đến bản đồ.")
    # G vẫn là None

# --- Decorator yêu cầu đăng nhập ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in_user' not in session:
            flash("Bạn cần đăng nhập để truy cập trang này.", "warning")
            return redirect(url_for('show_login_form'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes cho xác thực người dùng ---
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
        return jsonify({"success": False, "message": "Tên đăng nhập đã tồn tại."}), 409 # Conflict
    
    # Trong thực tế: hash mật khẩu trước khi lưu
    users_db[username] = {"password": password, "email": email}
    print(f"Người dùng mới đăng ký: {username}, Cơ sở dữ liệu người dùng hiện tại: {users_db}") # Log để kiểm tra
    return jsonify({"success": True, "message": "Đăng ký thành công! Vui lòng đăng nhập."}), 201 # Created

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

@app.route('/bounds')
@login_required
def get_bounds():
    if not GRAPH_LOADED_SUCCESSFULLY or G is None:
        return jsonify({'error': 'Dữ liệu bản đồ chưa được tải thành công.'}), 503
    try:
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
        if edges_gdf.empty and nodes_gdf.empty:
             return jsonify({'error': 'Đồ thị không có nút hoặc cạnh nào để xác định ranh giới.'}), 404
        
        # Lấy ranh giới từ tất cả các nút và cạnh
        # Nếu không có cạnh, total_bounds của edges_gdf có thể gây lỗi hoặc không chính xác
        # Nếu không có nút, total_bounds của nodes_gdf có thể gây lỗi
        
        if not nodes_gdf.empty:
            bounds_nodes = nodes_gdf.total_bounds # minx, miny, maxx, maxy
            # bounds trả về: [min_lat, min_lon, max_lat, max_lon]
            # total_bounds của GeoDataFrame: [minx, miny, maxx, maxy] -> [lon_min, lat_min, lon_max, lat_max]
            # Vậy: [bounds_nodes[1], bounds_nodes[0], bounds_nodes[3], bounds_nodes[2]]
            return jsonify({'bounds': [bounds_nodes[1], bounds_nodes[0], bounds_nodes[3], bounds_nodes[2]]})
        elif not edges_gdf.empty : # Nếu chỉ có cạnh mà không có nút (ít khả năng)
            bounds_edges = edges_gdf.total_bounds
            return jsonify({'bounds': [bounds_edges[1], bounds_edges[0], bounds_edges[3], bounds_edges[2]]})
        else: # Trường hợp đồ thị hoàn toàn rỗng
            return jsonify({'error': 'Đồ thị rỗng, không thể xác định ranh giới.'}), 404

    except Exception as e:
        print(f"Lỗi khi lấy bounds: {e}")
        return jsonify({'error': str(e), 'message': 'Không thể lấy ranh giới đồ thị'}), 500


@app.route('/route')
@login_required
def get_route_api(): # Đổi tên hàm để tránh trùng với module 'route' có thể có
    if not GRAPH_LOADED_SUCCESSFULLY or G is None:
        return jsonify({'error': 'Dữ liệu bản đồ chưa được tải. Không thể tìm đường.'}), 503
    try:
        orig_lat = float(request.args.get('orig_lat'))
        orig_lon = float(request.args.get('orig_lon'))
        dest_lat = float(request.args.get('dest_lat'))
        dest_lon = float(request.args.get('dest_lon'))

        # Sử dụng hàm tìm node gần nhất bằng Haversine từ pathfinding.py
        orig_node = find_nearest_node_haversine(G, orig_lon, orig_lat)
        dest_node = find_nearest_node_haversine(G, dest_lon, dest_lat)

        if orig_node is None or dest_node is None:
             return jsonify({'error': 'Không thể tìm thấy nút bắt đầu hoặc kết thúc trên bản đồ.'}), 400
        
        if orig_node == dest_node:
             node_coords = (G.nodes[orig_node]['y'], G.nodes[orig_node]['x'])
             return jsonify({'route': [node_coords], 'distance': 0, 'message': 'Điểm bắt đầu và kết thúc trùng nhau.'})

        route_nodes = astar_path_custom(G, orig_node, dest_node, heuristic_func=heuristic, weight='length')

        if route_nodes is None:
            return jsonify({'error': 'Không tìm thấy đường đi giữa hai điểm đã cho.'}), 404

        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route_nodes]
        
        total_distance = 0
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i+1]
            edge_data_dict = G.get_edge_data(u, v)
            if edge_data_dict:
                min_length_edge = float('inf')
                for key in edge_data_dict:
                    if 'length' in edge_data_dict[key]:
                         min_length_edge = min(min_length_edge, edge_data_dict[key]['length'])
                if min_length_edge != float('inf'):
                    total_distance += min_length_edge
        return jsonify({'route': route_coords, 'distance': total_distance})
    except ValueError:
        return jsonify({'error': 'Dữ liệu tọa độ không hợp lệ.'}), 400
    except Exception as e:
        print(f"Lỗi trong API /route: {e}")
        return jsonify({'error': f'Đã xảy ra lỗi không mong muốn: {str(e)}'}), 500

if __name__ == '__main__':
    # Chạy app. Không cần debug=True và use_reloader=False nếu không có vấn đề tải G lặp lại
    # Flask sẽ tự động dùng reloader khi debug=True
    app.run(debug=True)