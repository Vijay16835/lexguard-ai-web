const winston = require('winston');
const path = require('path');
const fs = require('fs-extra');
const config = require('../config/config');

fs.ensureDirSync(config.dirs.logs);

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.printf(({ timestamp, level, message }) => `[${timestamp}] [${level.toUpperCase()}]: ${message}`)
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message }) => `[${timestamp}] ${level}: ${message}`)
      )
    }),
    new winston.transports.File({
      filename: path.join(config.dirs.logs, 'automation.log'),
      level: 'info'
    }),
    new winston.transports.File({
      filename: path.join(config.dirs.logs, 'error.log'),
      level: 'error'
    })
  ]
});

module.exports = logger;
