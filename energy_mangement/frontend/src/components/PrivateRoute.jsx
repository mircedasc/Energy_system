import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const PrivateRoute = ({ children, allowedRoles }) => {
    const { user, token, loading } = useContext(AuthContext);

    // Cât timp verificăm token-ul, nu afișăm nimic (sau un spinner)
    if (loading) {
        return <div>Loading...</div>;
    }

    // 1. Nu e logat -> Redirect la Login
    if (!token || !user) {
        return <Navigate to="/login" />;
    }

    // 2. E logat, dar nu are rolul cerut -> Redirect la Client
    if (allowedRoles && !allowedRoles.includes(user.role)) {
        return <Navigate to="/client" />;
    }

    // 3. Totul e ok -> Afișează pagina
    return children;
};

export default PrivateRoute;