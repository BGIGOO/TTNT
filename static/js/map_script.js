const map = L.map('map').setView([10.848015315160042, 106.78667009709487], 15); // Zoom out một chút
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let markers = [];
    let routeLine;
    const center = { lat: 10.762622, lng: 106.660172 };
    const maxDist = 30; // km, bạn có thể đặt lại nếu cần kiểm tra khoảng cách

    const startInput = document.getElementById('start');
    const endInput = document.getElementById('end');
    const dynamicSuggestionsContainer = document.getElementById('dynamic-suggestions-list-container');
    const estimatedTimeEl = document.getElementById('estimated-time');
    const totalDistanceEl = document.getElementById('total-distance');


    function addMarker(latlng, label, inputToUpdate) {
      const marker = L.marker(latlng).addTo(map).bindPopup(label).openPopup();
      markers.push(marker);
      if (inputToUpdate) {
        inputToUpdate.value = `${latlng[0].toFixed(6)}, ${latlng[1].toFixed(6)}`;
        inputToUpdate.dataset.selectedLat = latlng[0];
        inputToUpdate.dataset.selectedLng = latlng[1];
      }
    }

    function drawRoute(routeData) {
      if (routeLine) map.removeLayer(routeLine);
      routeLine = L.polyline(routeData.route, { color: 'blue' }).addTo(map);
      map.fitBounds(routeLine.getBounds());

      if (routeData.distance_km !== undefined && routeData.estimated_time_minutes !== undefined) {
        totalDistanceEl.textContent = routeData.distance_km + " Km";
        estimatedTimeEl.textContent = routeData.estimated_time_minutes + " Phút";

        console.log("đã nhảy vô đây11111")
      } else {
        console.log("đã nhảy vô2222222")
        // Tính toán dự phòng phía client nếu backend không trả về
        let totalDistanceKmClient = 0;
        for (let i = 0; i < routeData.route.length - 1; i++) {
// Lần lặp 1 (i = 0):
// Tính khoảng cách giữa [10.8464548, 106.7855988] và [10.8465679, 106.7864017].
// Kết quả: distance1 = 89.5 mét.
// Lần lặp 2 (i = 1):
// Tính khoảng cách giữa [10.8465679, 106.7864017] và [10.8465821, 106.7868126].
// Kết quả: distance2 = 45.3 mét.

            totalDistanceKmClient += L.latLng(routeData.route[i]).distanceTo(L.latLng(routeData.route[i+1]));
        }
        totalDistanceKmClient = totalDistanceKmClient / 1000;
        totalDistanceEl.textContent = totalDistanceKmClient.toFixed(3) + " Km";

        const averageSpeedKmph = 20; // Tốc độ đi bộ trung bình
        const estimatedTimeHours = totalDistanceKmClient / averageSpeedKmph;
        estimatedTimeEl.textContent = Math.round(estimatedTimeHours * 60) + " Phút";
      }
    }

    async function geocode(address) {
      // Ưu tiên tìm kiếm gần vị trí trung tâm bản đồ hoặc vị trí hiện tại (nếu có)
      const url = `https://photon.komoot.io/api/?q=${encodeURIComponent(address)}&lat=${center.lat}&lon=${center.lng}&limit=7`;
      try {
        const res = await fetch(url);
        const data = await res.json();
        const suggestionsList = [];
        data.features.forEach(f => {
          let name = f.properties.name;
          let details = [f.properties.street, f.properties.housenumber, f.properties.district, f.properties.city, f.properties.country]
                         .filter(Boolean).join(', ');
          if (!name) name = details; // Nếu không có tên cụ thể, dùng chi tiết làm tên

          if(name) {
              suggestionsList.push({
                  name: name,
                  // Hiển thị chi tiết hơn nếu khác với tên chính
                  details: (details && details !== name) ? details : (f.properties.osm_value || ''),
                  lat: f.geometry.coordinates[1],
                  lng: f.geometry.coordinates[0]
              });
          }
        });
        return suggestionsList;
      } catch (error) {
        console.error("Geocoding error:", error);
        return [];
      }
    }

    async function geocodeAndRoute() {
      const startLat = startInput.dataset.selectedLat;
      const startLng = startInput.dataset.selectedLng;
      const endLat = endInput.dataset.selectedLat;
      const endLng = endInput.dataset.selectedLng;

      if (!startLat || !startLng || !endLat || !endLng) {
        alert("Vui lòng chọn điểm đến và điểm đi (bằng cách nhập hoặc click trên bản đồ).");
        return;
      }

      // Xóa gợi ý đang hiển thị
      dynamicSuggestionsContainer.innerHTML = '';

      // Thêm marker nếu chưa có (ví dụ: người dùng chỉ nhập text và chưa click)
      // Cần kiểm tra xem marker có tương ứng với input không, nếu không thì tạo mới/cập nhật
      // Để đơn giản, ta giả định nếu có lat/lng thì marker đã được xử lý bởi click hoặc người dùng không cần marker cho text input
      // Tuy nhiên, để trực quan hơn, ta nên đảm bảo marker được hiển thị:
      markers.forEach(m => map.removeLayer(m)); // Xóa marker cũ trước
      markers = [];
      addMarker([parseFloat(startLat), parseFloat(startLng)], "Điểm đi: " + startInput.value);
      addMarker([parseFloat(endLat), parseFloat(endLng)], "Điểm đến: " + endInput.value);


      const url = `/route?orig_lat=${startLat}&orig_lon=${startLng}&dest_lat=${endLat}&dest_lon=${endLng}`;
      $.getJSON(url, data => {
        if (data.route && data.route.length > 0) {

            console.log("Route data du lieu:", data);

            drawRoute(data); // data giờ chứa cả route, distance_km, estimated_time_minutes
        } else {
            alert(data.error || "Không tìm thấy đường đi. Vui lòng thử lại với các điểm khác.");
            totalDistanceEl.textContent = "-- Km";
            estimatedTimeEl.textContent = "-- Phút";
        }
      }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Route API error:", textStatus, errorThrown, jqXHR.responseText);
            alert("Có lỗi xảy ra khi tìm đường. Vui lòng kiểm tra backend và thử lại.");
            totalDistanceEl.textContent = "-- Km";
            estimatedTimeEl.textContent = "-- Phút";
      });
    }

    function displaySuggestions(results, inputElement) {
        dynamicSuggestionsContainer.innerHTML = ''; // Xóa gợi ý cũ

        if (results.length > 0 && inputElement.value.length >=2) {
            results.forEach(r => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.innerHTML = `${r.name}<br><small style='color:gray;'>${r.details || ''}</small>`;
                div.onclick = () => {
                    inputElement.value = r.name;
                    inputElement.dataset.selectedLat = r.lat;
                    inputElement.dataset.selectedLng = r.lng;
                    dynamicSuggestionsContainer.innerHTML = ''; // Xóa danh sách khi đã chọn

                    // Tự động tìm đường nếu cả hai điểm đã được chọn
                    if (startInput.dataset.selectedLat && endInput.dataset.selectedLat) {
                        geocodeAndRoute();
                    }
                };
                dynamicSuggestionsContainer.appendChild(div);
            });
        }
    }

    function setupAutocomplete(inputElement) {
      let debounceTimer;
      inputElement.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(async () => {
            const text = inputElement.value;
            // Xóa tọa độ đã lưu nếu người dùng sửa input thủ công
            delete inputElement.dataset.selectedLat;
            delete inputElement.dataset.selectedLng;
            // Giữ lại marker và route cho đến khi "xác nhận" hoặc chọn điểm mới
            // totalDistanceEl.textContent = "-- Km";
            // estimatedTimeEl.textContent = "-- Phút";

            if (text.length < 2) {
              dynamicSuggestionsContainer.innerHTML = '';
              return;
            }
            const results = await geocode(text);
            displaySuggestions(results, inputElement);
        }, 300);
      });
        // Đóng danh sách gợi ý khi click ra ngoài danh sách và không phải là input
        document.addEventListener('click', function(event) {
            const isClickInsideInput = inputElement.contains(event.target);
            const isClickInsideSuggestions = dynamicSuggestionsContainer.contains(event.target);
            if (!isClickInsideInput && !isClickInsideSuggestions) {
                dynamicSuggestionsContainer.innerHTML = '';
            }
        });
    }

    setupAutocomplete(startInput);
    setupAutocomplete(endInput);

    // --- KHÔI PHỤC CHỨC NĂNG CLICK TRÊN BẢN ĐỒ ---
    map.on('click', function(e) {
      const clickedLat = e.latlng.lat;
      const clickedLng = e.latlng.lng;

      // Ưu tiên điền vào ô input chưa có giá trị hoặc ô "start" trước
      let targetInput;
      let label;

      if (!startInput.dataset.selectedLat || markers.length === 0) {
        targetInput = startInput;
        label = "Điểm đi đã chọn";
        // Nếu đã có 2 marker, đây là lượt chọn mới, xóa hết
        if (markers.length >= 2) {
            clearAllData(false); // false để không reset view bản đồ ngay
        }
      } else if (!endInput.dataset.selectedLat || markers.length === 1) {
        targetInput = endInput;
        label = "Điểm đi đã chọn";
      } else { // Cả hai input đã có, hoặc đã có 2 marker -> bắt đầu lại từ điểm "start"
        clearAllData(false);
        targetInput = startInput;
        label = "Điểm đi đã chọn";
      }

      // Xóa marker tương ứng nếu đang cập nhật lại điểm đó
      if (targetInput === startInput && markers.length > 0) {
          const oldStartMarker = markers.find(m => m.getPopup().getContent().startsWith("Điểm đến"));
          if (oldStartMarker) {
              map.removeLayer(oldStartMarker);
              markers = markers.filter(m => m !== oldStartMarker);
          }
      } else if (targetInput === endInput && markers.length > 0) {
           const oldEndMarker = markers.find(m => m.getPopup().getContent().startsWith("Điểm đến"));
           if (oldEndMarker) {
              map.removeLayer(oldEndMarker);
              markers = markers.filter(m => m !== oldEndMarker);
           }
      }
       // Nếu đã có 2 marker và đang chọn lại, cần xóa bớt marker cho đúng
      if (markers.length >= 2) { // Trường hợp click lần 3 trở đi, reset và coi như điểm đầu
          markers.forEach(m => map.removeLayer(m));
          markers = [];
          if (routeLine) map.removeLayer(routeLine);

          delete startInput.dataset.selectedLat;
          delete startInput.dataset.selectedLng;
          startInput.value = '';
          delete endInput.dataset.selectedLat;
          delete endInput.dataset.selectedLng;
          endInput.value = '';
          totalDistanceEl.textContent = "-- Km";
          estimatedTimeEl.textContent = "-- Phút";
          // Đặt lại targetInput là start
          targetInput = startInput;
          label = "Điểm đến đã chọn";
      }


      addMarker([clickedLat, clickedLng], label, targetInput);
      dynamicSuggestionsContainer.innerHTML = ''; // Xóa gợi ý khi chọn trên bản đồ

      // Nếu cả hai điểm đã được chọn qua click (hoặc kết hợp text và click)
      if (startInput.dataset.selectedLat && endInput.dataset.selectedLat) {
        geocodeAndRoute();
      }
    });

    function clearAllData(resetView = true) {
      markers.forEach(m => map.removeLayer(m));
      markers = [];
      if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
      }
      startInput.value = '';
      endInput.value = '';
      delete startInput.dataset.selectedLat;
      delete startInput.dataset.selectedLng;
      delete endInput.dataset.selectedLat;
      delete endInput.dataset.selectedLng;
      totalDistanceEl.textContent = "-- Km";
      estimatedTimeEl.textContent = "-- Phút";
      dynamicSuggestionsContainer.innerHTML = '';
      if (resetView) {
        map.setView([10.848015315160042, 106.78667009709487], 13);
      }
    }