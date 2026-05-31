const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const nodemailer = require('nodemailer');
const pool = require('../config/db');

// JWT Secrets configuration
const JWT_SECRET = process.env.JWT_SECRET || 'super_secret_jwt_key_lexguard';
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'super_secret_refresh_key_lexguard';

// Nodemailer configuration
const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: process.env.SMTP_PORT,
    secure: process.env.SMTP_SECURE === 'true',
    auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
    },
});

// Helper Function: Generate Tokens
const generateTokens = (user) => {
    const payload = { id: user.id, email: user.email, full_name: user.full_name };
    const accessToken = jwt.sign(payload, JWT_SECRET, { expiresIn: '15m' }); // Short-lived access token
    const refreshToken = jwt.sign(payload, JWT_REFRESH_SECRET, { expiresIn: '7d' }); // Long-lived refresh token
    return { accessToken, refreshToken };
};

// 1. SIGNUP
router.post('/signup', async (req, res) => {
    const { email, password, full_name } = req.body;
    try {
        // Check if user exists
        const userCheck = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
        if (userCheck.rows.length > 0) {
            return res.status(400).json({ success: false, message: 'Email already registered' });
        }

        // Hash password
        const salt = await bcrypt.genSalt(10);
        const passwordHash = await bcrypt.hash(password, salt);

        // Insert new user
        const result = await pool.query(
            'INSERT INTO users (email, password_hash, full_name, auth_provider) VALUES ($1, $2, $3, $4) RETURNING id, email, full_name, is_verified',
            [email, passwordHash, full_name, 'local']
        );
        
        const user = result.rows[0];

        // Send OTP for Verification automatically
        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        const expiresAt = new Date(Date.now() + 10 * 60000); // 10 minutes

        await pool.query(
            'INSERT INTO otp_verifications (user_id, email, otp_code, purpose, expires_at) VALUES ($1, $2, $3, $4, $5)',
            [user.id, email, otp, 'signup', expiresAt]
        );

        await transporter.sendMail({
            from: process.env.SMTP_USER,
            to: email,
            subject: 'Verify Your LexGuard AI Account',
            text: `Your verification OTP is ${otp}. It will expire in 10 minutes.`,
            html: `<p>Your verification OTP is <b>${otp}</b>. It will expire in 10 minutes.</p>`
        });

        res.json({ success: true, message: 'Signup successful. Please verify your email with the OTP sent.', data: { user } });
    } catch (error) {
        console.error('Signup Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error during signup' });
    }
});

// 2. VERIFY OTP
router.post('/verify-otp', async (req, res) => {
    const { email, otp } = req.body;
    try {
        const otpRecord = await pool.query(
            'SELECT * FROM otp_verifications WHERE email = $1 AND otp_code = $2 AND is_used = false AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1',
            [email, otp]
        );

        if (otpRecord.rows.length === 0) {
            return res.status(400).json({ success: false, message: 'Invalid or expired OTP' });
        }

        const record = otpRecord.rows[0];

        // Mark OTP as used
        await pool.query('UPDATE otp_verifications SET is_used = true WHERE id = $1', [record.id]);

        // If signup purpose, verify the user
        if (record.purpose === 'signup') {
            await pool.query('UPDATE users SET is_verified = true WHERE email = $1', [email]);
        }

        // Get user and generate tokens
        const userResult = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
        const user = userResult.rows[0];

        const { accessToken, refreshToken } = generateTokens(user);

        // Store refresh token
        await pool.query(
            'INSERT INTO sessions (user_id, refresh_token, expires_at) VALUES ($1, $2, NOW() + INTERVAL \'7 days\')',
            [user.id, refreshToken]
        );

        res.json({
            success: true,
            message: 'Verification successful',
            data: { access_token: accessToken, refresh_token: refreshToken, user: { id: user.id, email: user.email, full_name: user.full_name } }
        });
    } catch (error) {
        console.error('Verify OTP Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error during verification' });
    }
});

// 2.5 SEND OTP (For Login Verification)
router.post('/send-otp', async (req, res) => {
    const { email } = req.body;
    try {
        const userResult = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
        if (userResult.rows.length === 0) {
            return res.status(404).json({ success: false, message: 'User not found' });
        }

        const user = userResult.rows[0];

        // Rate limiting check
        const recentOtp = await pool.query(
            'SELECT * FROM otp_verifications WHERE email = $1 AND purpose = \'login_verification\' AND created_at > NOW() - INTERVAL \'1 minute\'',
            [email]
        );

        if (recentOtp.rows.length > 0) {
            return res.status(429).json({ success: false, message: 'Please wait 1 minute before requesting another OTP.' });
        }

        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        const expiresAt = new Date(Date.now() + 10 * 60000);

        await pool.query(
            'INSERT INTO otp_verifications (user_id, email, otp_code, purpose, expires_at) VALUES ($1, $2, $3, $4, $5)',
            [user.id, email, otp, 'login_verification', expiresAt]
        );

        await transporter.sendMail({
            from: process.env.SMTP_USER,
            to: email,
            subject: 'Login OTP Verification',
            text: `Your login OTP is ${otp}. It will expire in 10 minutes.`,
            html: `<p>Your login OTP is <b>${otp}</b>. It will expire in 10 minutes.</p>`
        });

        res.json({ success: true, message: 'OTP sent successfully' });
    } catch (error) {
        console.error('Send OTP Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

// 3. LOGIN
router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    try {
        const userResult = await pool.query('SELECT * FROM users WHERE email = $1 AND auth_provider = \'local\'', [email]);
        if (userResult.rows.length === 0) {
            return res.status(401).json({ success: false, message: 'Invalid credentials' });
        }

        const user = userResult.rows[0];

        const isMatch = await bcrypt.compare(password, user.password_hash);
        if (!isMatch) {
            return res.status(401).json({ success: false, message: 'Invalid credentials' });
        }

        if (!user.is_verified) {
            return res.status(403).json({ success: false, message: 'Email not verified. Please request a new OTP.' });
        }

        const { accessToken, refreshToken } = generateTokens(user);

        await pool.query(
            'INSERT INTO sessions (user_id, refresh_token, expires_at) VALUES ($1, $2, NOW() + INTERVAL \'7 days\')',
            [user.id, refreshToken]
        );

        res.json({
            success: true,
            data: { access_token: accessToken, refresh_token: refreshToken, user: { id: user.id, email: user.email, full_name: user.full_name } }
        });
    } catch (error) {
        console.error('Login Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error during login' });
    }
});

// 4. FORGOT PASSWORD (SEND OTP)
router.post('/forgot-password', async (req, res) => {
    const { email } = req.body;
    try {
        const userResult = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
        if (userResult.rows.length === 0) {
            return res.status(404).json({ success: false, message: 'User not found' });
        }

        const user = userResult.rows[0];

        // Rate limiting check
        const recentOtp = await pool.query(
            'SELECT * FROM otp_verifications WHERE email = $1 AND purpose = \'forgot_password\' AND created_at > NOW() - INTERVAL \'1 minute\'',
            [email]
        );

        if (recentOtp.rows.length > 0) {
            return res.status(429).json({ success: false, message: 'Please wait 1 minute before requesting another OTP.' });
        }

        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        const expiresAt = new Date(Date.now() + 10 * 60000);

        await pool.query(
            'INSERT INTO otp_verifications (user_id, email, otp_code, purpose, expires_at) VALUES ($1, $2, $3, $4, $5)',
            [user.id, email, otp, 'forgot_password', expiresAt]
        );

        await transporter.sendMail({
            from: process.env.SMTP_USER,
            to: email,
            subject: 'Password Reset OTP',
            text: `Your password reset OTP is ${otp}. It will expire in 10 minutes.`,
            html: `<p>Your password reset OTP is <b>${otp}</b>. It will expire in 10 minutes.</p>`
        });

        res.json({ success: true, message: 'OTP sent successfully' });
    } catch (error) {
        console.error('Forgot Password Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

// 5. RESET PASSWORD
router.post('/reset-password', async (req, res) => {
    const { email, otp, new_password } = req.body;
    try {
        const otpRecord = await pool.query(
            'SELECT * FROM otp_verifications WHERE email = $1 AND otp_code = $2 AND purpose = \'forgot_password\' AND is_used = false AND expires_at > NOW()',
            [email, otp]
        );

        if (otpRecord.rows.length === 0) {
            return res.status(400).json({ success: false, message: 'Invalid or expired OTP' });
        }

        const salt = await bcrypt.genSalt(10);
        const passwordHash = await bcrypt.hash(new_password, salt);

        // Update password
        await pool.query('UPDATE users SET password_hash = $1 WHERE email = $2', [passwordHash, email]);

        // Mark OTP as used
        await pool.query('UPDATE otp_verifications SET is_used = true WHERE id = $1', [otpRecord.rows[0].id]);

        // Optional: Revoke all existing sessions for security
        await pool.query('UPDATE sessions SET is_revoked = true WHERE user_id = $1', [otpRecord.rows[0].user_id]);

        res.json({ success: true, message: 'Password reset successful' });
    } catch (error) {
        console.error('Reset Password Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

// 6. GOOGLE AUTH (Firebase ID Token verification assumed on client, we receive email here)
// In a true prod app, you MUST verify the id_token via firebase-admin SDK here!
router.post('/google-auth', async (req, res) => {
    const { id_token, email, full_name, profile_image } = req.body;
    try {
        if (!email) {
            return res.status(400).json({ success: false, message: 'Email required' });
        }

        let userResult = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
        let user;

        if (userResult.rows.length === 0) {
            // Register new Google user
            const result = await pool.query(
                'INSERT INTO users (email, full_name, avatar_url, is_verified, auth_provider) VALUES ($1, $2, $3, true, $4) RETURNING *',
                [email, full_name, profile_image, 'google']
            );
            user = result.rows[0];
        } else {
            user = userResult.rows[0];
        }

        const { accessToken, refreshToken } = generateTokens(user);

        await pool.query(
            'INSERT INTO sessions (user_id, refresh_token, expires_at) VALUES ($1, $2, NOW() + INTERVAL \'7 days\')',
            [user.id, refreshToken]
        );

        res.json({
            success: true,
            data: { access_token: accessToken, refresh_token: refreshToken, user: { id: user.id, email: user.email, full_name: user.full_name, avatarUrl: user.avatar_url } }
        });
    } catch (error) {
        console.error('Google Auth Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

// 7. REFRESH TOKEN
router.post('/refresh-token', async (req, res) => {
    const { refresh_token } = req.body;
    if (!refresh_token) return res.status(403).json({ success: false, message: 'Refresh token required' });

    try {
        // Check database if revoked
        const sessionCheck = await pool.query('SELECT * FROM sessions WHERE refresh_token = $1 AND is_revoked = false AND expires_at > NOW()', [refresh_token]);
        
        if (sessionCheck.rows.length === 0) {
            return res.status(403).json({ success: false, message: 'Invalid or expired refresh token' });
        }

        jwt.verify(refresh_token, JWT_REFRESH_SECRET, async (err, decoded) => {
            if (err) return res.status(403).json({ success: false, message: 'Refresh token expired' });

            const userResult = await pool.query('SELECT * FROM users WHERE id = $1', [decoded.id]);
            const user = userResult.rows[0];

            const accessToken = jwt.sign({ id: user.id, email: user.email, full_name: user.full_name }, JWT_SECRET, { expiresIn: '15m' });
            
            res.json({ success: true, data: { access_token: accessToken } });
        });
    } catch (error) {
        console.error('Refresh Token Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

// 8. LOGOUT
router.post('/logout', async (req, res) => {
    const { refresh_token } = req.body;
    try {
        if (refresh_token) {
            await pool.query('UPDATE sessions SET is_revoked = true WHERE refresh_token = $1', [refresh_token]);
        }
        res.json({ success: true, message: 'Logged out successfully' });
    } catch (error) {
        console.error('Logout Error:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
});

module.exports = router;
