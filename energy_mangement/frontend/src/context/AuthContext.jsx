import { createContext, useState, useEffect, useContext } from 'react'; // 1. Am adăugat useContext
import { jwtDecode } from "jwt-decode";
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        if (token) {
            try {
                const decoded = jwtDecode(token);
                // Verificăm expirarea (exp e în secunde)
                if (decoded.exp * 1000 < Date.now()) {
                    logout();
                } else {
                    setUser(decoded);
                }
            } catch (error) {
                console.error("Invalid token", error);
                logout();
            }
        }
        setLoading(false);
    }, [token]);

    const login = (newToken) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        const decoded = jwtDecode(newToken);
        setUser(decoded);

        if (decoded.role === "Administrator") {
            navigate('/admin');
        } else {
            navigate('/client');
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        navigate('/login');
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

// 2. ACEASTA ESTE PARTEA CARE LIPSEA ȘI PROVOCA EROAREA
// Exportăm un hook custom ca să nu mai scriem useContext(AuthContext) peste tot
export const useAuth = () => {
    return useContext(AuthContext);
};

export default AuthContext;