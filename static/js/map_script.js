// static/js/map_script.js
// (Nội dung file script.js bạn đã cung cấp, phiên bản cập nhật với hiển thị km)
// ... (Toàn bộ code của file script.js hiện tại của bạn)

// Biến giữ đối tượng bản đồ Leaflet
const map = L.map('map' /* Đảm bảo id này có trong map_page.html */); // Sẽ setView sau khi có bounds

// Thêm lớp bản đồ OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let danhSachDiemDanhDau = [];
let duongDanVe;

function veDuongDi(duongDi) {
  if (duongDanVe) map.removeLayer(duongDanVe);
  if (duongDi && duongDi.length > 0) {
      duongDanVe = L.polyline(duongDi, { color: 'blue' }).addTo(map);
      if (duongDanVe.getBounds().isValid()) {
        map.fitBounds(duongDanVe.getBounds(), {
            maxZoom: 16,
            padding: [50, 50]
        });
      }
  } else {
      $('#routeDistance').text("---");
  }
}

function themDiemDanhDau(toaDo, nhan) {
  const diemDanhDau = L.marker(toaDo).addTo(map).bindPopup(nhan).openPopup();
  danhSachDiemDanhDau.push(diemDanhDau);
}

// Lấy ranh giới từ server và thiết lập bản đồ
$.getJSON('/bounds', function(data) {
    if (data && data.bounds) {
        const bounds = data.bounds;
        map.fitBounds([
            [bounds[0], bounds[1]],
            [bounds[2], bounds[3]]
        ]);
    } else {
        map.setView([10.762622, 106.660172], 13); // Fallback
    }
}).fail(function() {
    map.setView([10.762622, 106.660172], 13); // Fallback
}).always(function() {
    map.invalidateSize();
});

map.on('click', function(e) {
  if (danhSachDiemDanhDau.length >= 2) {
    danhSachDiemDanhDau.forEach(diem => map.removeLayer(diem));
    if (duongDanVe) map.removeLayer(duongDanVe);
    duongDanVe = null;
    danhSachDiemDanhDau = [];
    $('#startPoint').val('');
    $('#endPoint').val('');
    $('#routeDistance').text("---");
    $('#routeTime').text("---");
  }

  const toaDoClick = [e.latlng.lat, e.latlng.lng];
  const toaDoString = `${toaDoClick[0].toFixed(6)}, ${toaDoClick[1].toFixed(6)}`;

  if (danhSachDiemDanhDau.length === 0) {
    themDiemDanhDau(toaDoClick, 'Xuất phát');
    $('#startPoint').val(toaDoString);
  } else if (danhSachDiemDanhDau.length === 1) {
    themDiemDanhDau(toaDoClick, 'Đích');
    $('#endPoint').val(toaDoString);
  }

  if (danhSachDiemDanhDau.length === 2) {
    const [diemBatDau, diemKetThuc] = danhSachDiemDanhDau.map(diem => diem.getLatLng());
    const url = `/route?orig_lat=${diemBatDau.lat}&orig_lon=${diemBatDau.lng}&dest_lat=${diemKetThuc.lat}&dest_lon=${diemKetThuc.lng}`;

    $.getJSON(url, function(duLieu) {
        if (duLieu && duLieu.route && duLieu.route.length > 0) {
            veDuongDi(duLieu.route);

            // Hiển thị quãng đường
            if (typeof duLieu.distance !== 'undefined') {
                const distanceInKm = (duLieu.distance / 1000).toFixed(2);
                $('#routeDistance').text(distanceInKm);
            } else {
                 $('#routeDistance').text("N/A");
            }

            // Hiển thị thời gian di chuyển dự kiến
            if (typeof duLieu.travel_time_seconds !== 'undefined') {
                const totalSeconds = parseInt(duLieu.travel_time_seconds, 10);
                if (totalSeconds > 0) {
                    const hours = Math.floor(totalSeconds / 3600);
                    const minutes = Math.floor((totalSeconds % 3600) / 60);
                    const seconds = totalSeconds % 60;

                    let timeString = "";
                    if (hours > 0) {
                        timeString += hours + " giờ ";
                    }
                    if (minutes > 0 || hours > 0) { // Hiển thị phút nếu có giờ hoặc có phút
                        timeString += minutes + " phút ";
                    }
                    // Chỉ hiển thị giây nếu thời gian < 1 phút, hoặc nếu muốn chi tiết hơn
                    if (hours === 0 && minutes === 0 && seconds > 0) {
                         timeString += seconds + " giây";
                    } else if (hours === 0 && minutes > 0 && seconds > 0) { // Thêm giây nếu có phút và giây > 0
                         timeString += seconds + " giây";
                    }


                    $('#routeTime').text(timeString.trim() || "Dưới 1 phút");
                } else if (totalSeconds === 0 && duLieu.distance === 0) { // Trường hợp điểm đầu cuối trùng nhau
                     $('#routeTime').text("0 phút");
                }
                 else {
                    $('#routeTime').text("Không đáng kể");
                }
            } else {
                 $('#routeTime').text("N/A");
            }

        } else if (duLieu && duLieu.error) {
            // ... (xử lý lỗi như cũ) ...
            $('#routeDistance').text("Lỗi");
            $('#routeTime').text("Lỗi"); // Reset thời gian khi có lỗi
        } else {
            // ... (xử lý không tìm thấy đường như cũ) ...
            $('#routeDistance').text("Không tìm thấy");
            $('#routeTime').text("Không tìm thấy"); // Reset thời gian
        }
    }).fail(function() {
        alert("Lỗi kết nối khi tìm đường.");
        $('#routeDistance').text("Lỗi kết nối");
    });
  }
});

$('#selectOnMapButton').on('click', function() {
    alert('Click vào bản đồ để chọn điểm Xuất phát (lần 1) và Đích đến (lần 2).');
});