import axios from 'axios';

// URL-ul este localhost pentru că Traefik (pe portul 80) preia cererile
// și le duce la microservicii (/auth, /users, /devices)
const api = axios.create({
    baseURL: 'http://localhost',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor: Adaugă automat Token-ul la fiecare cerere, dacă există
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

export default api;