# core_logic/pathfinding.py

import heapq
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances
import math

#Công thức Haversine được dùng để tính khoảng cách theo
#đường tròn lớn giữa hai điểm trên bề mặt Trái Đất,
#dựa vào vĩ độ và kinh độ của hai điểm đó.
#Đây là công thức thường dùng trong hệ thống định vị GPS.
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Bán kính Trái Đất (mét)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

#Khoảng cách Manhattan là tổng khoảng cách theo chiều ngang và chiều dọc
def manhattan(lat1, lon1, lat2, lon2):
    # Đổi độ thành khoảng cách gần đúng theo mét
    # 1 độ vĩ độ ≈ 111.32 km, kinh độ tùy vĩ độ
    lat_dist = abs(lat2 - lat1) * 111320  # mét

    # Khoảng cách 1 độ kinh độ thay đổi theo vĩ độ
    avg_lat = math.radians((lat1 + lat2) / 2)
    lon_per_deg = 111320 * math.cos(avg_lat)  # mét
    lon_dist = abs(lon2 - lon1) * lon_per_deg

    return lat_dist + lon_dist  # khoảng cách Manhattan ước lượng theo mét

#Giống Manhattan, nhưng thay vì cộng lat_dist + lon_dist, ta lấy lớn nhất.
#khoảng cách Chebyshev là khoảng cách lớn nhất giữa hai điểm trong không gian Euclidean.
def chebyshev(lat1, lon1, lat2, lon2):
    # Ước lượng độ dài mỗi độ vĩ độ và kinh độ
    lat_dist = abs(lat2 - lat1) * 111320  # mét

    avg_lat = math.radians((lat1 + lat2) / 2)
    lon_per_deg = 111320 * math.cos(avg_lat)  # mét
    lon_dist = abs(lon2 - lon1) * lon_per_deg

    return max(lat_dist, lon_dist)

# Cách đo:	    Hành trình:	                                Kết quả (ước lượng):
# Manhattan	    Đi dọc → rồi ngang	                        ~550 m
# Haversine	    Bay thẳng như chim	                        ~390 m
# Chebyshev	    Tối đa giữa dọc và ngang (cho phép đi chéo)	~328 m

def find_nearest_node_haversine(graph, x, y):
    """
    Tìm nút gần nhất trong đồ thị với một điểm tọa độ (lon, lat) cho trước,
    sử dụng công thức Haversine.
    """
    nearest_node_id = None
    min_dist = float('inf')

    for node_id, data in graph.nodes(data=True):
        node_lon = data['x']
        node_lat = data['y']
        distance = haversine(y, x, node_lat, node_lon) # lat1, lon1, lat2, lon2
        if distance < min_dist:
            min_dist = distance
            nearest_node_id = node_id
    return nearest_node_id

#dùng euclidean_distances giả sử trái đất phẳng 2d
def heuristic1(graph, u_id, v_id): 
    """
    Hàm heuristic ước tính chi phí từ u_id đến v_id.
    Sử dụng khoảng cách Euclidean
    Lưu ý: Để chính xác hơn về mặt địa lý, có thể dùng Haversine,
    nhưng Euclidean thường đủ tốt cho A* nếu tọa độ là chiếu (projected).
    """
    if u_id not in graph.nodes or v_id not in graph.nodes:
        return float('inf')
    
    u_node_data = graph.nodes[u_id]
    v_node_data = graph.nodes[v_id]

    if 'x' not in u_node_data or 'y' not in u_node_data or \
       'x' not in v_node_data or 'y' not in v_node_data:
        return float('inf')

    u_point = np.array([[u_node_data['y'], u_node_data['x']]]) # lat, lon
    v_point = np.array([[v_node_data['y'], v_node_data['x']]]) # lat, lon

    return euclidean_distances(u_point, v_point)[0][0]

def heuristic2(graph, u_id, v_id): 
    """
    Hàm heuristic ước tính chi phí từ u_id đến v_id bằng Manhattan.
    """
    if u_id not in graph.nodes or v_id not in graph.nodes:
        return float('inf')
    
    u_node_data = graph.nodes[u_id]
    v_node_data = graph.nodes[v_id]

    if 'x' not in u_node_data or 'y' not in u_node_data or \
       'x' not in v_node_data or 'y' not in v_node_data:
        return float('inf')

    lat1, lon1 = u_node_data['y'], u_node_data['x']
    lat2, lon2 = v_node_data['y'], v_node_data['x']

    return manhattan(lat1, lon1, lat2, lon2)

def heuristic3(graph, u_id, v_id): 
    """
    Hàm heuristic ước tính chi phí từ u_id đến v_id bằng Chebyshev.
    """
    if u_id not in graph.nodes or v_id not in graph.nodes:
        return float('inf')
    
    u_node_data = graph.nodes[u_id]
    v_node_data = graph.nodes[v_id]

    if 'x' not in u_node_data or 'y' not in u_node_data or \
       'x' not in v_node_data or 'y' not in v_node_data:
        return float('inf')

    lat1, lon1 = u_node_data['y'], u_node_data['x']
    lat2, lon2 = v_node_data['y'], v_node_data['x']

    return chebyshev(lat1, lon1, lat2, lon2)

def heuristic4(graph, u_id, v_id): 
    """
    Hàm heuristic ước tính chi phí từ u_id đến v_id bằng Haversine.
    """
    if u_id not in graph.nodes or v_id not in graph.nodes:
        return float('inf')
    
    u_node_data = graph.nodes[u_id]
    v_node_data = graph.nodes[v_id]

    if 'x' not in u_node_data or 'y' not in u_node_data or \
       'x' not in v_node_data or 'y' not in v_node_data:
        return float('inf')

    lat1, lon1 = u_node_data['y'], u_node_data['x']
    lat2, lon2 = v_node_data['y'], v_node_data['x']

    return haversine(lat1, lon1, lat2, lon2)


#Chạy A*
def astar_path_custom(graph, start_node, end_node, heuristic_func, weight='length'):
    open = []
    heapq.heappush(open, (0, start_node))
    open_set_lookup = {start_node}  # Tập để kiểm tra nhanh xem node đã có trong hàng đợi chưa vì heapq không hỗ trợ xóa phần tử bất kỳ
    prev = {}  # Để truy vết đường đi ngược lại khi tìm ra đích
    g_score = {node: float('inf') for node in graph.nodes() } # Khởi tạo g_score cho tất cả các node = vô cực
    g_score[start_node] = 0
    f_score = {node: float('inf') for node in graph.nodes()} # Khởi tạo f_score cho tất cả các node = vô cực
    f_score[start_node] = heuristic_func(graph, start_node, end_node)
    while open:
        _, current_node = heapq.heappop(open) # Lấy node có f_score nhỏ nhất
        if current_node not in open_set_lookup: #Kiểm tra nếu current_node đã bị xử lý rồi thì bỏ qua.
                                                #(heapq có thể chứa nhiều bản sao cùng node → tránh lặp lại)
            continue
        open_set_lookup.remove(current_node) #Nếu chưa, xóa node khỏi open_set_lookup để đánh dấu là đã xử lý.

        if current_node == end_node:
            path = []
            temp = current_node
            while temp in prev:
                path.append(temp)
                temp = prev[temp]
            path.append(start_node)
            #print(f"Đường đi từ {start_node} đến {end_node}: {path[::-1]} \n")
            return path[::-1]   # Đảo ngược để đúng thứ tự start → end
        

        for neighbor in graph.neighbors(current_node):  #Duyệt các node kề với current_node
            #print(f"Đang duyệt các node kề với {current_node}: {graph.neighbors(current_node)}\n")
            edge_data_all = graph.get_edge_data(current_node, neighbor)
            # Lấy tất cả các thuộc tính của cạnh giữa current_node và neighbor
            if not edge_data_all:
                continue

            Cost_current_neighbor = float('inf') #Tính g_score giữa current_node và neighbor
            for edge_key in edge_data_all:
                edge_attributes = edge_data_all[edge_key]
                # đồ thị có thể có nhiều cạnh giữa 2 node
                # Lấy cạnh có chi phí thấp nhất (min theo trọng số weight, mặc định là 'length').
                if weight in edge_attributes:
                    Cost_current_neighbor = min(Cost_current_neighbor, edge_attributes[weight])
            if Cost_current_neighbor == float('inf'):
                continue
            
            tentative_g_score = g_score[current_node] + Cost_current_neighbor #Tính chi phí mới đến neighbor thông qua current_node.

            # Nếu chi phí mới nhỏ hơn giá trị đã biết, thì cập nhật.
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                prev[neighbor] = current_node
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic_func(graph, neighbor, end_node)
                if neighbor not in open_set_lookup: # Nếu neighbor chưa được xét, thêm vào open để chờ xét trong tương lai.
                    heapq.heappush(open, (f_score[neighbor], neighbor))
                    open_set_lookup.add(neighbor)
    return None

#Chạy A* với heuristic=0 (tức là Dijkstra).
def Dijkstra(graph, start_node, end_node, heuristic_func, weight='length'):
    open_set = []
    heapq.heappush(open_set, (0, start_node))
    open_set_lookup = {start_node}
    came_from = {}
    g_score = {node: float('inf') for node in graph.nodes()}
    g_score[start_node] = 0
    f_score = {node: float('inf') for node in graph.nodes()}
    f_score[start_node] = 0

    while open_set:
        _, current_node = heapq.heappop(open_set)
        
        if current_node not in open_set_lookup:
            continue
        open_set_lookup.remove(current_node)

        if current_node == end_node:
            path = []
            temp = current_node
            while temp in came_from:
                path.append(temp)
                temp = came_from[temp]
            path.append(start_node)
            return path[::-1]

        for neighbor in graph.neighbors(current_node):
            edge_data_all = graph.get_edge_data(current_node, neighbor)
            if not edge_data_all:
                continue

            min_edge_weight = float('inf')
            for edge_key in edge_data_all: 
                edge_attributes = edge_data_all[edge_key]
                if weight in edge_attributes:
                    min_edge_weight = min(min_edge_weight, edge_attributes[weight])
            
            if min_edge_weight == float('inf'):
                continue
            
            tentative_g_score = g_score[current_node] + min_edge_weight

            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + 0 #heuristic_func(graph, neighbor, end_node)
                if neighbor not in open_set_lookup:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_lookup.add(neighbor)
    return None