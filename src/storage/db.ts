import Database from 'better-sqlite3';
import { config } from '../config';
import * as fs from 'fs';
import * as path from 'path';

export class QuantDatabase {
    private db: Database.Database;

    constructor() {
        const dbPath = config.database.path;
        const dbDir = path.dirname(dbPath);

        if (!fs.existsSync(dbDir)) {
            fs.mkdirSync(dbDir, { recursive: true });
        }

        this.db = new Database(dbPath);
        this.initSchema();
    }

    private initSchema() {
        // Events table (Significant movements)
        this.db.exec(`
      CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        severity TEXT NOT NULL,
        significance_score REAL,
        timestamp INTEGER NOT NULL,
        data TEXT NOT NULL, -- JSON
        summary TEXT
      );
      CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
      CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
    `);

        // Snapshots table (Periodic states)
        this.db.exec(`
      CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        type TEXT NOT NULL,
        data TEXT NOT NULL -- JSON
      );
      CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp);
    `);

        // Patterns table (Learned info)
        this.db.exec(`
      CREATE TABLE IF NOT EXISTS patterns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        confidence REAL,
        last_seen INTEGER,
        frequency INTEGER DEFAULT 1,
        data TEXT -- JSON definition
      );
    `);

        // Reports table
        this.db.exec(`
      CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        period_start INTEGER NOT NULL,
        period_end INTEGER NOT NULL,
        summary TEXT,
        content TEXT -- Markdown/JSON
      );
    `);

        console.log('Database schema initialized');
    }

    public getDb(): Database.Database {
        return this.db;
    }

    public insertEvent(event: any) {
        const stmt = this.db.prepare(`
      INSERT INTO events (id, type, severity, significance_score, timestamp, data, summary)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(event.id, event.type, event.severity, event.significanceScore, event.timestamp, JSON.stringify(event.data), event.summary);
    }
}
