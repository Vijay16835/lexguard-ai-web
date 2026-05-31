const express = require('express');
const router = express.Router();
const { verifyToken } = require('../middleware/authMiddleware');
const pool = require('../config/db');

// Get current user profile
router.get('/me', verifyToken, async (req, res) => {
    try {
        const userResult = await pool.query(
            'SELECT id, email, full_name, avatar_url, is_verified, auth_provider, created_at FROM users WHERE id = $1',
            [req.user.id]
        );

        if (userResult.rows.length === 0) {
            return res.status(404).json({ success: false, message: 'User not found' });
        }

        res.json({ success: true, data: userResult.rows[0] });
    } catch (error) {
        console.error('Get User Profile Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

module.exports = router;
