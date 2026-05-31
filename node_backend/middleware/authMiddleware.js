const jwt = require('jsonwebtoken');

const verifyToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    if (!authHeader) {
        return res.status(403).json({ success: false, message: 'No token provided' });
    }

    const token = authHeader.split(' ')[1]; // Format: Bearer <token>
    if (!token) {
        return res.status(403).json({ success: false, message: 'Invalid token format' });
    }

    jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
        if (err) {
            return res.status(401).json({ success: false, message: 'Unauthorized! Token expired or invalid.' });
        }
        req.user = decoded; // Contains id, email, etc.
        next();
    });
};

module.exports = { verifyToken };
