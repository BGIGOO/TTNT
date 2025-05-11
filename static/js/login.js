// static/js/login.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const messageDiv = document.getElementById('message'); // Thêm một div để hiển thị thông báo

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());

            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(result => {
                if (messageDiv) messageDiv.textContent = ''; // Xóa thông báo cũ
                if (result.success) {
                    window.location.href = '/map'; // Chuyển hướng đến trang bản đồ
                } else {
                    if (messageDiv) messageDiv.textContent = result.message || 'Đăng nhập thất bại.';
                    else alert(result.message || 'Đăng nhập thất bại.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (messageDiv) messageDiv.textContent = 'Lỗi kết nối. Vui lòng thử lại.';
                else alert('Lỗi kết nối. Vui lòng thử lại.');
            });
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(registerForm);
            const data = Object.fromEntries(formData.entries());

            if (data.new_password !== data.confirm_password) {
                if (messageDiv) messageDiv.textContent = 'Mật khẩu xác nhận không khớp.';
                else alert('Mật khẩu xác nhận không khớp.');
                return;
            }

            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: data.new_username,
                    password: data.new_password,
                    email: data.email
                }),
            })
            .then(response => response.json())
            .then(result => {
                if (messageDiv) messageDiv.textContent = ''; // Xóa thông báo cũ
                if (result.success) {
                    if (messageDiv) messageDiv.textContent = result.message || 'Đăng ký thành công! Vui lòng đăng nhập.';
                    else alert(result.message || 'Đăng ký thành công! Vui lòng đăng nhập.');
                    toggleForm(); // Chuyển về form đăng nhập
                    loginForm.reset(); // Xóa các trường của form đăng nhập (nếu muốn)
                    registerForm.reset(); // Xóa các trường của form đăng ký
                } else {
                    if (messageDiv) messageDiv.textContent = result.message || 'Đăng ký thất bại.';
                    else alert(result.message || 'Đăng ký thất bại.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (messageDiv) messageDiv.textContent = 'Lỗi kết nối. Vui lòng thử lại.';
                else alert('Lỗi kết nối. Vui lòng thử lại.');
            });
        });
    }
});

function toggleForm() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const messageDiv = document.getElementById('message');

    loginForm.classList.toggle('hidden');
    registerForm.classList.toggle('hidden');
    if (messageDiv) messageDiv.textContent = ''; // Xóa thông báo khi chuyển form
}