<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PyBackup – Production Backup Engine</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        :root {
            --primary: #2563eb;
            --secondary: #0f172a;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
            --accent: #22c55e;
            --border: #e5e7eb;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
        }

        header {
            background: linear-gradient(135deg, var(--primary), #1d4ed8);
            color: #fff;
            padding: 60px 20px;
            text-align: center;
        }

        header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
        }

        header p {
            font-size: 1.2rem;
            max-width: 900px;
            margin: 0 auto;
            opacity: 0.95;
        }

        main {
            max-width: 1100px;
            margin: 40px auto;
            padding: 0 20px;
        }

        section {
            background: var(--card);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
        }

        section h2 {
            margin-top: 0;
            color: var(--secondary);
            border-bottom: 2px solid var(--border);
            padding-bottom: 8px;
        }

        ul {
            padding-left: 20px;
        }

        ul li {
            margin-bottom: 8px;
        }

        .badge {
            display: inline-block;
            background: #eef2ff;
            color: var(--primary);
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 0.9rem;
            margin: 5px 5px 5px 0;
        }

        pre {
            background: #0f172a;
            color: #e5e7eb;
            padding: 16px;
            border-radius: 10px;
            overflow-x: auto;
            font-size: 0.9rem;
        }

        code {
            font-family: "JetBrains Mono", monospace;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        footer {
            text-align: center;
            padding: 30px 20px;
            color: var(--muted);
            font-size: 0.9rem;
        }

        .highlight {
            color: var(--accent);
            font-weight: 600;
        }

        @media (max-width: 600px) {
            header h1 {
                font-size: 2.2rem;
            }
        }
    </style>
</head>
<body>

<header>
    <h1>PyBackup</h1>
    <p>
        A production-ready Python CLI tool for automated backup of files, databases,
        and system configurations.
    </p>
</header>

<main>

    <section>
        <h2>Overview</h2>
        <p>
            PyBackup is a lightweight, extensible backup engine designed for Linux servers
            and DevOps environments.
        </p>
        <p>
            It solves the problem of managing <strong>multiple backup types</strong>
            using a single, unified configuration and command-line interface.
        </p>

        <p><strong>Intended for:</strong></p>
        <ul>
            <li>System Administrators</li>
            <li>DevOps Engineers</li>
            <li>Backend Developers</li>
            <li>Small to medium production environments</li>
        </ul>

        <p>
            The goal is to provide a <span class="highlight">simple, scriptable,
            and reliable backup solution</span> without vendor lock-in.
        </p>
    </section>

    <section>
        <h2>Features</h2>
        <div class="grid">
            <ul>
                <li>YAML-based configuration</li>
                <li>CLI-driven execution</li>
                <li>File & config backups</li>
                <li>Backup verification & checksums</li>
            </ul>
            <ul>
                <li>MongoDB backups</li>
                <li>PostgreSQL backups</li>
                <li>MySQL backups</li>
                <li>MS SQL Server backups</li>
            </ul>
            <ul>
                <li>Env-based secret handling</li>
                <li>Cron & systemd friendly</li>
                <li>Modular architecture</li>
                <li>Production-safe logging</li>
            </ul>
        </div>
    </section>

    <section>
        <h2>Installation</h2>
        <h3>Using pip</h3>
        <pre><code>pip install pybackup</code></pre>

        <h3>From source</h3>
        <pre><code>git clone https://github.com/selvaraj2003/pybackup.git
cd pybackup
pip install .</code></pre>
    </section>

    <section>
        <h2>Requirements</h2>
        <ul>
            <li>Python 3.9+</li>
            <li>Linux (recommended)</li>
            <li>mongodump</li>
            <li>pg_dump</li>
            <li>mysqldump</li>
            <li>sqlcmd (MS SQL Server)</li>
        </ul>
    </section>

    <section>
        <h2>Configuration</h2>
        <pre><code>version: 1
global:
  backup_root: /backups
  retention_days: 7
  log_level: INFO

files:
  enabled: true
  jobs:
    - name: nginx_config
      source: /etc/nginx
      output: /backups/files/nginx</code></pre>

        <p>Secrets are provided via environment variables.</p>
    </section>

    <section>
        <h2>Usage</h2>
        <pre><code>pybackup --help</code></pre>
        <pre><code>pybackup run --config /etc/pybackup/pybackup.yaml</code></pre>
    </section>

    <section>
        <h2>Scheduling</h2>
        <h3>Cron</h3>
        <pre><code>0 2 * * * /usr/bin/pybackup run --config /etc/pybackup/pybackup.yaml</code></pre>

        <h3>Systemd</h3>
        <pre><code>[Unit]
Description=PyBackup Service

[Service]
ExecStart=/usr/bin/pybackup run --config /etc/pybackup/pybackup.yaml
Restart=on-failure

[Install]
WantedBy=multi-user.target</code></pre>
    </section>

    <section>
        <h2>Project Structure</h2>
        <pre><code>pybackup/
├── pybackup/
│   ├── cli.py
│   ├── engine/
│   ├── config/
│   ├── utils/
│   └── constants.py
├── tests/
├── scripts/
├── examples/
├── README.md
└── pyproject.toml</code></pre>
    </section>

    <section>
        <h2>License</h2>
        <p>MIT License © 2026 Selvaraj Iyyappan</p>
    </section>

</main>

</body>
</html>