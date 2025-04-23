module.exports = {
  apps: [{
    name: "trump-monitor",
    script: "trump_tweet_monitor.py",
    interpreter: "python3",
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: "200M",
    log_date_format: "YYYY-MM-DD HH:mm:ss",
    env: {
      NODE_ENV: "production",
    },
    // 启动失败时的重试策略
    max_restarts: 10,
    min_uptime: "20s",
    restart_delay: 4000,
    // 日志配置
    out_file: "pm2_trump_out.log",
    error_file: "pm2_trump_error.log",
    merge_logs: true,
    // 在控制台输出时间戳
    time: true
  }]
}; 