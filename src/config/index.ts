import { AgentConfig } from '../types';
import * as fs from 'fs';
import * as path from 'path';
import dotenv from 'dotenv'; // Import dotenv

dotenv.config();

const defaultConfigPath = path.resolve(__dirname, '../../config/default.json');
const rawConfig = JSON.parse(fs.readFileSync(defaultConfigPath, 'utf-8'));

// Override with env vars (basic example)
if (process.env.MVX_API_URL) rawConfig.api.baseUrl = process.env.MVX_API_URL;
if (process.env.SLACK_WEBHOOK) rawConfig.notifications.slack.webhookUrl = process.env.SLACK_WEBHOOK;

export const config: AgentConfig = rawConfig as AgentConfig;
